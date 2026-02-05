from abc import ABC, abstractmethod
import asyncio
from services.event_bus import EventBus
from utils.logger import get_logger

logger = get_logger(__name__)

class BaseService(ABC):
    """
    Abstract base class for all asynchronous services.
    Handles lifecycle management and event bus dependency injection.
    """

    def __init__(self, name: str, event_bus: EventBus):
        """
        Initialize the service.
        
        :param name: Unique name for the service.
        :param event_bus: Injected instance of EventBus.
        """
        self.name = name
        self.bus = event_bus
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Start the service by creating an asynchronous task."""
        if self._running:
            logger.warning(f"[{self.name}] Service is already running.")
            return
            
        self._running = True
        logger.info(f"[{self.name}] Starting service...")
        self._task = asyncio.create_task(self._run_wrapper())

    async def _run_wrapper(self):
        """Internal wrapper to handle setup, execution, and cleanup phases."""
        try:
            await self.setup()
            await self.run()
        except asyncio.CancelledError:
            logger.debug(f"[{self.name}] Task successfully cancelled.")
        except Exception as e:
            logger.exception(f"[{self.name}] Critical error in service: {e}")
        finally:
            await self.cleanup()
            self._running = False

    async def stop(self):
        """Stop the service and wait for the task to finish."""
        if not self._running:
            return
            
        logger.info(f"[{self.name}] Stopping service...")
        self._running = False
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None

    async def setup(self):
        """Optional setup logic to be overridden by subclasses."""
        pass

    async def cleanup(self):
        """Optional cleanup logic to be overridden by subclasses."""
        pass

    @abstractmethod
    async def run(self) -> None:
        """Main execution loop to be implemented by concrete services."""
        pass