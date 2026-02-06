import asyncio
from collections import deque
import time
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Callable, Any, Dict, Optional

from services.event_bus import EventBus
from .base_service import BaseService
from utils.logger import get_logger

# Import CORS settings from config
try:
    from config import (ALLOWED_ORIGINS, ALLOWED_CREDENTIALS, ALLOWED_METHODS, ALLOWED_HEADERS,
                        POT_TOPIC, MODE_CHANGE_TOPIC)
except ImportError:
    ALLOWED_ORIGINS = ["*"]
    ALLOWED_CREDENTIALS = True
    ALLOWED_METHODS = ["*"]
    ALLOWED_HEADERS = ["*"]
    POT_TOPIC = "pot"
    MODE_CHANGE_TOPIC = "mode_change"

logger = get_logger(__name__)


class HttpService(BaseService):
    """
    HTTP Infrastructure Adapter.
    Exposes REST API with FastAPI, translates HTTP POST/PUT into EventBus publications,
    and publishes periodic data to EventBus topics.
    """

    def __init__(self, event_bus: EventBus, host: str = "0.0.0.0", port: int = 8000,
                 publish_interval: float = 10.0, api_prefix: str = "/api/v1"):
        super().__init__("http_service", event_bus)
        self.host = host
        self.port = port
        self._publish_interval = publish_interval
        self._last_publish_time = 0.0
        self._api_prefix = api_prefix.rstrip("/")
        self._latest_received: Dict[str, Any] = {}

        self._publish_topics: Dict[str, Callable[[], Any]] = {}

        # FastAPI app
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
        # GET endpoints
        @self._app.get(f"{self._api_prefix}/mode")
        async def get_mode():
            return {"mode": self._latest_received.get("mode"), "timestamp": time.time()}

        @self._app.get(f"{self._api_prefix}/levels")
        async def get_levels():
            return {"levels": self._latest_received.get("levels", []), "timestamp": time.time()}

        @self._app.get(f"{self._api_prefix}/valve")
        async def get_valve():
            return {"valve": self._latest_received.get("valve", 0.0), "timestamp": time.time()}

        # POST endpoints
        @self._app.post(f"{self._api_prefix}/pot")
        async def set_valve(payload: dict):
            pot = payload.get("pot")
            if pot is not None:
                self.bus.publish(POT_TOPIC, pot=pot)
                return {"status": "success", "sent": pot}
            return {"status": "error", "message": "Missing pot value"}, 400

        @self._app.post(f"{self._api_prefix}/change")
        async def set_btn(payload: dict):
            btn = payload.get("btn", False)
            if btn:
                self.bus.publish(MODE_CHANGE_TOPIC, btn=btn)
                return {"status": "success", "sent": btn}
            return {"status": "error", "message": "Button not pressed"}, 400

    # ===================== Periodic publishing =====================
    def configure_periodic_publishing(self, topic: str, data_generator: Callable):
        """
        Configura pubblicazione periodica su un topic.
        :param topic: Topic del bus
        :param data_generator: Funzione che ritorna il payload
        """
        self._publish_topics[topic] = data_generator
        logger.info(f"[{self.name}] Periodic publishing configured for topic '{topic}'")

    async def _periodic_publish(self):
        """Pubblica dati periodicamente sui topic configurati."""
        for topic, generator in self._publish_topics.items():
            try:
                data = generator() if callable(generator) else generator
                self.bus.publish(topic, **data)
                logger.debug(f"[{self.name}] Periodic publish to '{topic}': {data}")
            except Exception as e:
                logger.error(f"[{self.name}] Error in periodic publish to '{topic}': {e}")

    # ===================== Service lifecycle =====================
    async def run(self):
        """Avvia il server Uvicorn + loop di pubblicazione periodica."""
        self._server_task = asyncio.create_task(self._run_server())

        while self._running:
            now = time.monotonic()
            if now - self._last_publish_time >= self._publish_interval:
                await self._periodic_publish()
                self._last_publish_time = now
            await asyncio.sleep(1)

        if self._server_task:
            await self._server_task

    async def _run_server(self):
        config_uvicorn = uvicorn.Config(
            app=self._app,
            host=self.host,
            port=self.port,
            log_level="info",
            loop="asyncio"
        )
        self._server = uvicorn.Server(config_uvicorn)
        try:
            await self._server.serve()
        except asyncio.CancelledError:
            logger.info(f"[{self.name}] Server task cancelled")
        except Exception as e:
            logger.error(f"[{self.name}] Uvicorn crashed: {e}")

    async def stop(self):
        """Arresto pulito del server Uvicorn."""
        if self._server:
            self._server.should_exit = True
        await super().stop()

    # ===================== Event Bus callbacks =====================
    def on_valve_update(self, opening: float):
        logger.info(f"[{self.name}] Valve update received: {opening}")
        self._latest_received["valve"] = opening

    def on_mode_update(self, mode: str):
        logger.info(f"[{self.name}] Mode update received: {mode}")
        self._latest_received["mode"] = mode

    def on_levels_out(self, levels: deque):
        logger.info(f"[{self.name}] Levels update received: {levels}")
        self._latest_received["levels"] = levels
