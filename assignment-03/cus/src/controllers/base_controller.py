from abc import ABC, abstractmethod
from typing import List
from services.base_service import BaseService
from utils.logger import get_logger
import asyncio

logger = get_logger(__name__)


class BaseController(ABC):
    """
    Generic abstract base controller for orchestrating services.
    
    Provides infrastructure for:
    - Managing multiple services lifecycle
    - Startup/shutdown hooks
    
    Does NOT assume specific service types (MQTT, HTTP, Serial).
    Subclasses define their own services and configuration logic.
    """

    def __init__(
        self,
        services: List[BaseService],
        event_dispatcher=None  # Deprecated, kept for compatibility
    ):
        """
        Initialize base controller with services.
        
        Args:
            services: List of services to manage
            event_dispatcher: (Deprecated) Not used with PyPubSub
        """
        self._services = services
        self._dispatcher = event_dispatcher  # Unused but kept for compatibility
        
        logger.info(f"{self.__class__.__name__} initialized with {len(services)} service(s)")
    
    # -------------------- Lifecycle management --------------------
    
    async def run(self) -> None:
        """
        Run the controller and all services.
        
        Template method that:
        1. Calls _on_start hook
        2. Starts all services concurrently
        """
        logger.info(f"Starting {self.__class__.__name__}")
        
        # Subclass hook
        await self._on_start()
        
        # Start all services (sets _running flag and creates tasks)
        for service in self._services:
            await service.start()
        
        # Wait for all service tasks to complete
        tasks = [service._task for service in self._services if service._task]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop(self) -> None:
        """
        Stop all services gracefully.
        
        Template method that:
        1. Calls _on_stop hook
        2. Stops all services
        """
        logger.info(f"Stopping {self.__class__.__name__}")
        
        # Subclass hook
        await self._on_stop()
        
        for service in self._services:
            await service.stop()
    
    # -------------------- Lifecycle Hooks --------------------
    @abstractmethod
    async def _on_start(self) -> None:
        """
        Hook called before services start.
        
        Override in subclass to perform initialization tasks
        (e.g., start watchdogs, initialize state).
        """
        pass

    @abstractmethod
    async def _on_stop(self) -> None:
        """
        Hook called before services stop.
        
        Override in subclass to perform cleanup tasks
        (e.g., stop watchdogs, save state).
        """
        pass
