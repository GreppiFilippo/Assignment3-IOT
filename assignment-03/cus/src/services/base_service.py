from abc import ABC, abstractmethod
import asyncio
from typing import Protocol, Any, List, Optional


class BaseModule(Protocol):
    """Protocol for service modules."""
    def start(self) -> None: ...
    def stop(self) -> None: ...


class BaseService(ABC):
    """Abstract base class for services with both sync and async lifecycle helpers.

    Concrete services can implement either `run()` (async) or override the
    synchronous `start()`/`stop()` pair. The base class provides helpers to
    run an async `run()` loop in a background task.
    """

    def __init__(self, service_name: str, event_bus: Optional[Any] = None):
        self.service_name: str = service_name
        self.event_bus = event_bus
        self.modules: List[BaseModule] = []
        self._task: Optional[asyncio.Task] = None
        self._running = False

    def add_module(self, module: BaseModule):
        self.modules.append(module)

    # --- synchronous compatibility API ---
    def start_modules(self):
        for m in self.modules:
            m.start()

    def stop_modules(self):
        for m in self.modules:
            m.stop()

    # --- async lifecycle API ---
    async def start(self):
        """Start the service. If `run()` is implemented, schedule it as a task."""
        if hasattr(self, "run") and asyncio.iscoroutinefunction(getattr(self, "run")):
            self._running = True
            self._task = asyncio.create_task(self.run())

    async def stop(self):
        """Stop the service and cancel the background task if present."""
        self._running = False
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None

    @abstractmethod
    async def run(self):
        """Async run loop for the service. Override in subclasses."""
        raise NotImplementedError()
