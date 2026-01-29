import asyncio
from typing import Any, Callable, Dict, List, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class Event:
    """
    Generic event object exchanged through the dispatcher.
    
    Args:
        topic: Event topic/channel identifier
        payload: Optional data associated with the event
    """

    def __init__(self, topic: str, payload: Any = None):
        self.topic = topic
        self.payload = payload

    def __repr__(self) -> str:
        return f"Event(topic='{self.topic}', payload={self.payload})"


class EventDispatcher:
    """
    Asynchronous event dispatcher implementing the publish-subscribe pattern.
    
    This dispatcher acts as a central message bus, allowing decoupled communication
    between system components. Services publish events to topics, and controllers
    or other components subscribe to topics of interest.
    """

    def __init__(self):
        """
        Initialize the event dispatcher.
            
        :param self: The instance
        """
        self._subscribers: Dict[str, List[Callable[[Event], Any]]] = {}
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False

        logger.info("EventDispatcher initialized")

    # ---------- Lifecycle management ----------

    async def start(self) -> None:
        """Start the event dispatcher loop."""
        if self._running:
            logger.warning("EventDispatcher already running")
            return
        logger.info("Starting EventDispatcher")
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        """Stop the event dispatcher and cancel pending events."""
        if not self._running:
            return
            
        logger.info("Stopping EventDispatcher")
        self._running = False

        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None
        
        logger.info("EventDispatcher stopped")

    # ---------- Subscription API ----------

    def subscribe(self, topic: str, callback: Callable[[Event], Any]) -> 'EventDispatcher':
        """
        Subscribe a callback to a specific event topic (Builder pattern).
        
        Args:
            topic: Topic to subscribe to (use "*" for all events)
            callback: Function to call when event is published (sync or async)
        
        Returns:
            Self for method chaining
        
        Example:
            dispatcher.subscribe("data", handle_data) \
                      .subscribe("error", handle_error)
        """
        self._subscribers.setdefault(topic, []).append(callback)
        logger.debug(f"Subscribed callback to topic '{topic}'")
        return self

    def unsubscribe(self, topic: str, callback: Callable[[Event], Any]) -> None:
        """
        Unsubscribe a callback from a specific event topic.
        
        Args:
            topic: Topic to unsubscribe from
            callback: Previously subscribed callback function
        """
        if topic in self._subscribers:
            try:
                self._subscribers[topic].remove(callback)
                logger.debug(f"Unsubscribed callback from topic '{topic}'")
            except ValueError:
                logger.warning(f"Callback not found for topic '{topic}'")

    # ---------- Publishing API ----------

    async def publish(self, topic: str, payload: Any = None) -> None:
        """
        Publish an event to a specific topic.
        
        Args:
            topic: Topic identifier
            payload: Optional data to send with the event
            
        Note:
            This is thread-safe and can be called from any thread.
        """
        if not self._running:
            logger.warning(f"Publishing event '{topic}' while dispatcher is not running")
        await self._queue.put(Event(topic, payload))
        logger.debug(f"Event '{topic}' queued for dispatch")

    # ---------- Internal event loop ----------

    async def _run(self) -> None:
        """Main event processing loop."""
        try:
            while self._running:
                event = await self._queue.get()

                # Get all subscribers for this topic + wildcard subscribers
                callbacks = (
                    self._subscribers.get(event.topic, []) +
                    self._subscribers.get("*", [])
                )

                if callbacks:
                    logger.debug(f"Dispatching {event} to {len(callbacks)} subscriber(s)")
                    for cb in callbacks:
                        self._dispatch_callback(cb, event)
                else:
                    logger.debug(f"No subscribers for event: {event}")

        except asyncio.CancelledError:
            logger.debug("EventDispatcher loop cancelled")
            raise

    def _dispatch_callback(self, callback: Callable[[Event], Any], event: Event) -> None:
        """
        Dispatch event to a single callback, handling both sync and async functions.
        
        Args:
            callback: The callback function to invoke
            event: The event to pass to the callback
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                # Async callback: schedule as task
                asyncio.create_task(callback(event))
            else:
                # Sync callback: run in executor to avoid blocking
                loop = asyncio.get_running_loop()
                loop.run_in_executor(None, callback, event)
        except Exception as exc:
            logger.exception(f"Error dispatching event '{event.topic}' to callback: {exc}")
