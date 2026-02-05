import asyncio
from collections import deque
from collections import deque
import time
import uvicorn
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Callable, Any, Dict, Optional
from functools import partial

from services.event_bus import EventBus
from .base_service import BaseService
from utils.logger import get_logger

# Import CORS settings from your config
try:
    from config import (ALLOWED_ORIGINS, ALLOWED_CREDENTIALS, ALLOWED_METHODS, ALLOWED_HEADERS)
except ImportError:
    # Fallback defaults if config is missing
    ALLOWED_ORIGINS = ["*"]
    ALLOWED_CREDENTIALS = True
    ALLOWED_METHODS = ["*"]
    ALLOWED_HEADERS = ["*"]

logger = get_logger(__name__)

class HttpService(BaseService):
    """
    HTTP Infrastructure Adapter.
    Exposes a REST API using FastAPI. It maps Event Bus topics to an internal 
    state that can be queried via HTTP GET, and translates HTTP POST/PUT 
    requests into Event Bus publications.
    """

    def __init__(self, event_bus: EventBus, host: str = "0.0.0.0", port: int = 8000, 
                 publish_interval: float = 10.0, api_prefix: str = ""):
        """
        Initialize the HTTP service.
        :param event_bus: Injected instance of CusEventBus.
        :param host: Server host address.
        :param port: Server port.
        :param publish_interval: Interval in seconds for periodic publishing.
        :param api_prefix: API prefix (e.g., "/api/v1")
        """
        super().__init__("http_service", event_bus)
        self.host = host
        self.port = port
        self._publish_interval = publish_interval
        self._last_publish_time = 0.0
        self._api_prefix = api_prefix.rstrip('/')  # Remove trailing slash
        self._latest_received: Dict[str, Any] = {}
        
        # FastAPI Application Setup
        self._app = FastAPI(
            title="Smart Tank System API",
            description="Interface for monitoring and controlling the system",
            version="1.0.0",
        )
        
        
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=ALLOWED_ORIGINS,
            allow_credentials=ALLOWED_CREDENTIALS,
            allow_methods=ALLOWED_METHODS,
            allow_headers=ALLOWED_HEADERS,
        )
        
        self._server: Optional[uvicorn.Server] = None
        self._server_task: Optional[asyncio.Task] = None
        self._publish_topics: Dict[str, Callable] = {}
        logger.info(f"[{self.name}] Initialized on {host}:{port}")

    def add_get_endpoint(self, path: str, state_key: str, response_key: Optional[str] = None):
        """
        Add a GET endpoint that returns data from internal state.
        :param path: URL path relative to api_prefix (e.g., "/mode")
        :param state_key: Key in _latest_received dict
        :param response_key: Key in response JSON (defaults to state_key)
        """
        if response_key is None:
            response_key = state_key
        
        full_path = f"{self._api_prefix}{path}"
            
        @self._app.get(full_path)
        async def get_endpoint():
            data = self._latest_received.get(state_key)
            return {
                response_key: data,
                "timestamp": time.time()
            }
        
        logger.info(f"[{self.name}] Registered GET {full_path} -> state[{state_key}]")
    
    def add_post_endpoint(self, path: str, bus_topic: str, payload_key: str):
        """
        Add a POST endpoint that publishes to the event bus.
        :param path: URL path relative to api_prefix (e.g., "/pot")
        :param bus_topic: Topic to publish on event bus
        :param payload_key: Key to extract from JSON payload
        """
        full_path = f"{self._api_prefix}{path}"
        
        @self._app.post(full_path)
        async def post_endpoint(payload: dict):
            data = payload.get(payload_key)
            if data is not None:
                self.bus.publish(bus_topic, **{payload_key: data})
                return {"status": "success", "sent": data}
            return {"status": "error", "message": f"Missing {payload_key}"}, 400
        
        logger.info(f"[{self.name}] Registered POST {full_path} -> bus[{bus_topic}]")
        
    
    def configure_periodic_publishing(self, topic: str, data_generator: Callable):
        """
        Configura pubblicazione periodica per un topic.
        
        :param topic: Topic del bus su cui pubblicare
        :param data_generator: Funzione che ritorna i dati da pubblicare
        """
        self._publish_topics[topic] = data_generator
        logger.info(f"[{self.name}] Periodic publishing configured for topic '{topic}'")

    async def run(self):
        """Starts the Uvicorn server + periodic publishing loop."""
        # Avvia il server Uvicorn in background
        self._server_task = asyncio.create_task(self._run_server())
        
        # Loop per pubblicazioni periodiche
        while self._running:
            now = time.monotonic()
            if now - self._last_publish_time >= self._publish_interval:
                await self._periodic_publish()
                self._last_publish_time = now
            await asyncio.sleep(1)
        
        # Aspetta che il server termini
        if self._server_task:
            await self._server_task
    
    async def _run_server(self):
        """Avvia il server Uvicorn."""
        config = uvicorn.Config(
            app=self._app,
            host=self.host,
            port=self.port,
            log_level="info",
            loop="asyncio"
        )
        self._server = uvicorn.Server(config)
        
        try:
            await self._server.serve()
        except asyncio.CancelledError:
            logger.info(f"[{self.name}] Server task cancelled.")
        except Exception as e:
            logger.error(f"[{self.name}] Uvicorn crashed: {e}")
    
    async def _periodic_publish(self):
        """Pubblica periodicamente su topic configurati."""
        for topic, generator in self._publish_topics.items():
            try:
                data = generator() if callable(generator) else generator
                self.bus.publish(topic, **data)
                logger.debug(f"[{self.name}] Periodic publish to '{topic}'")
            except Exception as e:
                logger.error(f"[{self.name}] Error in periodic publish to '{topic}': {e}")

    async def stop(self):
        """Gracefully shut down the Uvicorn server."""
        if self._server:
            self._server.should_exit = True
            # The base class stop() will cancel the task, which triggers serve() cleanup
        await super().stop()

    
    def on_state_update(self, state_key: str, **kwargs):
        """
        Generic callback to update internal state.
        :param state_key: Key to store in _latest_received
        :param kwargs: Data to store
        """
        # If single value, extract it
        if len(kwargs) == 1:
            self._latest_received[state_key] = list(kwargs.values())[0]
        else:
            self._latest_received[state_key] = kwargs
        logger.debug(f"[{self.name}] State updated: {state_key} = {self._latest_received[state_key]}")
