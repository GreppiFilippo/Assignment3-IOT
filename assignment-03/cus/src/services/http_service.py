import asyncio
import time
import uvicorn
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Callable, Any, Dict, List, Optional

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
                 publish_interval: float = 10.0):
        """
        Initialize the HTTP service.
        
        :param event_bus: Injected instance of CusEventBus.
        :param host: Server host address.
        :param port: Server port.
        :param publish_interval: Interval in seconds for periodic publishing.
        """
        super().__init__("http_service", event_bus)
        self.host = host
        self.port = port
        self._publish_interval = publish_interval
        self._last_publish_time = 0.0
        
        # Internal state to hold the latest data from the Bus
        self._state: Dict[str, Any] = {}
        # Periodic publishing: topic -> data generator callable
        self._publish_topics: Dict[str, Callable] = {}
        
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
        logger.info(f"[{self.name}] Initialized on {host}:{port}")

    def configure_messaging(self, watched_topics: Optional[List[str]] = None):
        """
        Define which Event Bus topics should update the internal API state.
        
        :param watched_topics: List of topics to subscribe to.
        """
        if watched_topics:
            for topic in watched_topics:
                # Crea callback dedicata per ogni topic
                callback = self._make_state_updater(topic)
                self.bus.subscribe(topic, callback)
                logger.info(f"[{self.name}] Watching topic: {topic}")

    def _make_state_updater(self, topic: str):
        """Factory per creare callback specifiche per ogni topic."""
        def handler(**kwargs):
            # Salva i dati sotto la chiave del topic
            if topic not in self._state:
                self._state[topic] = {}
            self._state[topic].update(kwargs)
            logger.debug(f"[{self.name}] State[{topic}] updated: {kwargs}")
        return handler

    def get_current_state(self) -> Dict[str, Any]:
        """Helper method for handlers to access the latest data."""
        return self._state

    def register_endpoint(self, method: str, path: str, handler: Callable):
        """
        Dynamically register a route. 
        Note: The handler can access self.get_current_state() or self.bus.publish().
        """
        method = method.upper()
        if method == "GET":
            self._app.get(path)(handler)
        elif method == "POST":
            self._app.post(path)(handler)
        # ... other methods ...
        return self
    
    def map_topic_to_endpoint(self, topic: str, method: str = "POST"):
        """
        Crea automaticamente un endpoint HTTP che pubblica sul topic specificato.
        
        :param topic: Topic del bus (es. "cmd.valve")
        :param method: Metodo HTTP ("POST" o "GET")
        
        Esempio:
            map_topic_to_endpoint("cmd.valve", "POST")
            → Crea POST /cmd/valve che pubblica su "cmd.valve"
        """
        path = f"/{topic.replace('.', '/')}"
        
        if method.upper() == "POST":
            @self._app.post(path)
            async def post_handler(data: Dict[str, Any] = Body(...)):
                logger.info(f"[{self.name}] POST {path} → bus.publish('{topic}')")
                self.bus.publish(topic, **data)
                return {"status": "ok", "topic": topic, "data": data}
        
        elif method.upper() == "GET":
            @self._app.get(path)
            async def get_handler():
                # Restituisce lo stato corrente per questo topic
                return {topic: self._state.get(topic, self._state)}
        
        logger.info(f"[{self.name}] Mapped {method.upper()} {path} → topic '{topic}'")
        return self
    
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