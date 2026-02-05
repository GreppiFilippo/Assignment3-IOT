from abc import ABC, abstractmethod
import asyncio
from pubsub import pub  # Assumendo l'uso di PyPubSub
from utils.logger import get_logger

logger = get_logger(__name__)

class BaseService(ABC):
    """
    Base class for services with lifecycle management and Pub/Sub integration.
    """

    def __init__(self, name: str):
        """
        Initialize the service with a given name.
        
        :param self: the instance itself
        :param name: the name of the service
        :type name: str
        """
        self.name = name
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Start the service lifecycle."""
        if self._running:
            logger.warning(f"[{self.name}] Already running.")
            return
        
        self._running = True
        # Register Pub/Sub listeners before starting the task
        self.subscribe_topics()
        self._task = asyncio.create_task(self._run_wrapper())
        logger.info(f"[{self.name}] Service started.")

    async def stop(self):
        """Stop the service and clean up resources."""
        if not self._running:
            return

        logger.info(f"[{self.name}] Shutting down...")
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        await self.cleanup()
        logger.info(f"[{self.name}] Service stopped.")

    async def _run_wrapper(self):
        """Wrapper to handle setup and main loop."""
        try:
            await self.setup()
            await self.run()
        except asyncio.CancelledError:
            logger.debug(f"[{self.name}] Task cancelled successfully.")
        except Exception as e:
            logger.exception(f"[{self.name}] Critical error: {e}")
        finally:
            self._running = False

    def subscribe_topics(self):
        """
        Override to register listeners (pub.subscribe).
        Called automatically on start().
        """
        pass

    async def setup(self):
        """Initialization logic (e.g., DB/Network connections)."""
        pass

    async def cleanup(self):
        """Cleanup logic (e.g., closing sockets)."""
        pass

    @abstractmethod
    async def run(self) -> None:
        """Main loop or waiting logic of the service."""
        pass