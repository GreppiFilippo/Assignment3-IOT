import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Callable, Any, Dict, List
from .base_service import BaseService
from .event_dispatcher import EventDispatcher
from utils.logger import get_logger
from config import (ALLOWED_ORIGINS, ALLOWED_CREDENTIALS, ALLOWED_METHODS, ALLOWED_HEADERS)

logger = get_logger(__name__)


class HttpService(BaseService):
    """
    HTTP service for exposing REST API endpoints.
    
    This service runs a FastAPI/Uvicorn server and allows dynamic registration
    of endpoint handlers, similar to how MQTTService registers message handlers.
    """

    def __init__(self, event_dispatcher: EventDispatcher, host: str = "0.0.0.0", port: int = 8000):
        """
        Initialize HTTP service.
        
        :param self: The instance
        :param event_dispatcher: Event dispatcher for inter-service communication
        :type event_dispatcher: EventDispatcher
        :param host: Server host address (default: "0.0.0.0")
        :type host: str
        :param port: Server port (default: 8000)
        :type port: int
        """
        super().__init__("http_service", event_dispatcher)
        self.host = host
        self.port = port
        
        self._app = FastAPI(
            title="Control Unit Subsystem API",
            description="REST API for the Smart Tank Monitoring System",
            version="1.0.0",
        )
        
        # CORS middleware for frontend
        self._app.add_middleware(
            CORSMiddleware,
            allow_origins=ALLOWED_ORIGINS,
            allow_credentials=ALLOWED_CREDENTIALS,
            allow_methods=ALLOWED_METHODS,
            allow_headers=ALLOWED_HEADERS,
        )
        
        self._server = None
        
        logger.info(f"{self.name} initialized on {host}:{port}")

    def register_endpoint(
        self, 
        method: str, 
        path: str, 
        handler: Callable[..., Any],
        **route_kwargs
    ) -> 'HttpService':
        """
        Register an HTTP endpoint handler (Builder pattern).
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: URL path (e.g., "/api/status")
            handler: Callback function (sync or async) to handle requests
            **route_kwargs: Additional FastAPI route parameters (response_model, etc.)
        
        Returns:
            Self for method chaining
        
        Example:
            http.register_endpoint("GET", "/status", get_status_handler) \
                .register_endpoint("POST", "/valve", set_valve_handler)
        """
        method = method.upper()
        
        if method == "GET":
            self._app.get(path, **route_kwargs)(handler)
        elif method == "POST":
            self._app.post(path, **route_kwargs)(handler)
        elif method == "PUT":
            self._app.put(path, **route_kwargs)(handler)
        elif method == "DELETE":
            self._app.delete(path, **route_kwargs)(handler)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        logger.info(f"{self.name} registered {method} {path}")
        return self

    async def run(self):
        """Run HTTP service with uvicorn server."""
        logger.info(f"{self.name} starting server on {self.host}:{self.port}")
        
        config = uvicorn.Config(
            app=self._app,
            host=self.host,
            port=self.port,
            log_level="info",
        )
        self._server = uvicorn.Server(config)
        
        try:
            await self._server.serve()
        except asyncio.CancelledError:
            logger.info(f"{self.name} server cancelled")
        finally:
            if self._server:
                await self._server.shutdown()
                
    async def stop(self):
        """Stop the HTTP server gracefully."""
        logger.info(f"{self.name} stopping server")
        if self._server:
            self._server.should_exit = True
        await super().stop()
