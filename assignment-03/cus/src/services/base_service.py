from abc import ABC, abstractmethod
import asyncio
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseService(ABC):
    """
    Abstract base class for all services (MQTT, Serial, HTTP, etc.).
    Handles async start/stop and controlled looping.
    """

    def __init__(self, name: str, event_dispatcher=None):
        """
        Initialize the service.
        
        :param name: Name of the service
        :param event_dispatcher: (Deprecated) Not used with PyPubSub
        """
        self.name = name
        self.event_dispatcher = event_dispatcher  # Keep for backward compat but unused
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Start the service by creating an async task."""
        if self._running:
            logger.warning(f"{self.name} is already running")
            return
        logger.info(f"Starting {self.name}")
        self._running = True
        # Wrapper handles exceptions and cancellation
        self._task = asyncio.create_task(self._run_wrapper())

    async def stop(self):
        """Stop the service cleanly."""
        if not self._running:
            logger.warning(f"{self.name} is already stopped")
            return
        logger.info(f"Stopping {self.name}")
        self._running = False
        if self._task:
            self._task.cancel()
            # Prevent unhandled exceptions on cancelled task
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None

    async def _run_wrapper(self):
        """
        Internal wrapper for the run() method.
        Catches exceptions and cancellation for safe execution.
        """
        try:
            await self.run()
        except asyncio.CancelledError:
            logger.info(f"{self.name} task cancelled")
        except Exception as e:
            logger.exception(f"Exception in {self.name}: {e}")

    @abstractmethod
    async def run(self) -> None:
        """
        Abstract method to be implemented by concrete services.
        Should use the self._running flag for controlled loops.
        """
        pass
