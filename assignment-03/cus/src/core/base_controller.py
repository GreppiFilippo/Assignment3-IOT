from abc import ABC, abstractmethod
from typing import List, Callable, Dict, Any
from services.base_service import BaseService
from services.event_dispatcher import EventDispatcher
from utils.logger import get_logger
import asyncio

logger = get_logger(__name__)


class BaseController(ABC):
    """
    Generic abstract base controller for orchestrating services.
    
    Provides infrastructure for:
    - Managing multiple services lifecycle
    - Event dispatcher integration
    - Startup/shutdown hooks
    
    Does NOT assume specific service types (MQTT, HTTP, Serial).
    Subclasses define their own services and configuration logic.
    """

    def __init__(
        self,
        services: List[BaseService],
        event_dispatcher: EventDispatcher
    ):
        """
        Initialize base controller with services.
        
        Args:
            services: List of services to manage
            event_dispatcher: Event dispatcher for inter-service communication
        """
        self._services = services
        self._dispatcher = event_dispatcher
        
        logger.info(f"{self.__class__.__name__} initialized with {len(services)} service(s)")
    
    # -------------------- Lifecycle management --------------------
    
    async def run(self) -> None:
        """
        Run the controller and all services.
        
        Template method that:
        1. Starts event dispatcher
        2. Calls _on_start hook
        3. Starts all services concurrently
        """
        logger.info(f"Starting {self.__class__.__name__}")
        await self._dispatcher.start()
        
        # Subclass hook
        await self._on_start()
        
        # Start all services as concurrent tasks
        tasks = [asyncio.create_task(service.run()) for service in self._services]
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self) -> None:
        """
        Stop all services gracefully.
        
        Template method that:
        1. Calls _on_stop hook
        2. Stops all services
        3. Stops event dispatcher
        """
        logger.info(f"Stopping {self.__class__.__name__}")
        
        # Subclass hook
        await self._on_stop()
        
        for service in self._services:
            await service.stop()
        await self._dispatcher.stop()
    
    # -------------------- Lifecycle Hooks --------------------
    
    async def _on_start(self) -> None:
        """
        Hook called before services start.
        
        Override in subclass to perform initialization tasks
        (e.g., start watchdogs, initialize state).
        """
        pass
    
    async def _on_stop(self) -> None:
        """
        Hook called before services stop.
        
        Override in subclass to perform cleanup tasks
        (e.g., stop watchdogs, save state).
        """
        pass
