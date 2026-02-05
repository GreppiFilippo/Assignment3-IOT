import asyncio
from collections import deque
from collections import deque
import time
import uvicorn
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Callable, Any, Dict, Optional
import config

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
        self._setup_routes()
        logger.info(f"[{self.name}] Initialized on {host}:{port}")

    def _setup_routes(self):
        # Usiamo il riferimento a self all'interno del decoratore
        @self._app.get("/api/v1/mode")
        async def get_mode():
            # Qui 'self' è accessibile perché get_mode è definita 
            # nel raggio d'azione (scope) di _setup_routes
            data = self._latest_received.get("mode")
            return {
                "mode": data,
                "timestamp": time.time()
            }
        
        @self._app.get("/api/v1/levels")
        async def get_levels():
            data = self._latest_received.get("levels", [])
            return {
                "levels": data,
                "timestamp": time.time()
            }
        
        @self._app.get("/api/v1/valve")
        async def get_valve():
            data = self._latest_received.get("valve", 0.0)
            return {
                "valve": data,
                "timestamp": time.time()
            }
        
        @self._app.post("/api/v1/pot")
        async def set_valve(payload: dict):
            """
            Riceve un JSON tipo: {"pot":{"val": X, "who": "source_id"}}
            E lo pubblica sull'Event Bus.
            """
            pot = payload.get("pot")
            
            if pot is not None:
                # PUBBLICHIAMO SUL BUS (Inverso di quello che facevi prima)
                # Il topic sarà quello che il Controller sta ascoltando
                self.bus.publish(config.POT_TOPIC, pot=pot)
                
                return {"status": "success", "sent": pot}
            
            return {"status": "error", "message": "Missing pot value"}, 400
        
        @self._app.post("/api/v1/change")
        async def set_btn(payload: dict):
            """
            Riceve un JSON tipo: {"btn": true}
            E lo pubblica sull'Event Bus.
            """
            btn = payload.get("btn", False)
            
            if btn:
                self.bus.publish(config.MODE_CHANGE_TOPIC, btn=btn)
                return {"status": "success", "sent": btn}
            
            return {"status": "error", "message": "Button not pressed"}, 400
        
    
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

    def on_valve_update(self, opening: float):
        """Callback for valve updates from the Event Bus."""
        logger.info(f"[{self.name}] Valve update received: {opening}")
        self._latest_received["valve"] = opening

    def on_mode_update(self, mode: str):
        """Callback for mode updates from the Event Bus."""
        logger.info(f"[{self.name}] Mode update received: {mode}")
        self._latest_received["mode"] = mode
    
    def on_levels_out(self, levels: deque):
        """Callback for levels updates from the Event Bus."""
        logger.info(f"[{self.name}] Levels update received: {levels}")
        self._latest_received["levels"] = levels