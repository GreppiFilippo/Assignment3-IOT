import asyncio
import uvicorn
from fastapi import FastAPI
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

    def __init__(self, event_bus: EventBus, host: str = "0.0.0.0", port: int = 8000):
        """
        Initialize the HTTP service.
        
        :param event_bus: Injected instance of CusEventBus.
        :param host: Server host address.
        :param port: Server port.
        """
        super().__init__("http_service", event_bus)
        self.host = host
        self.port = port
        
        # Internal state to hold the latest data from the Bus
        self._state: Dict[str, Any] = {}
        
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
        logger.info(f"[{self.name}] Initialized on {host}:{port}")

    def configure_messaging(self, watched_topics: List[str]):
        """
        Define which Event Bus topics should update the internal API state.
        
        :param watched_topics: List of topics to subscribe to.
        """
        for topic in watched_topics:
            self.bus.subscribe(topic, self._update_internal_state)
            logger.info(f"[{self.name}] API now watching topic: {topic}")

    def _update_internal_state(self, **kwargs):
        """Callback that refreshes the local state with data from the Bus."""
        # We merge the incoming event data into our local state dictionary
        self._state.update(kwargs)
        logger.debug(f"[{self.name}] Internal state updated: {self._state}")

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

    async def run(self):
        """Starts the Uvicorn server within the asyncio event loop."""
        config = uvicorn.Config(
            app=self._app,
            host=self.host,
            port=self.port,
            log_level="info",
            loop="asyncio" # Ensure it uses the same loop
        )
        self._server = uvicorn.Server(config)
        
        try:
            # serve() is a coroutine that runs the server until it stops
            await self._server.serve()
        except asyncio.CancelledError:
            logger.info(f"[{self.name}] Server task cancelled.")
        except Exception as e:
            logger.error(f"[{self.name}] Uvicorn crashed: {e}")

    async def stop(self):
        """Gracefully shut down the Uvicorn server."""
        if self._server:
            self._server.should_exit = True
            # The base class stop() will cancel the task, which triggers serve() cleanup
        await super().stop()