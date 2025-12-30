import asyncio
from typing import Any, Callable, Dict, List


class Event:
    def __init__(self, topic: str, payload: Any = None):
        self.topic = topic
        self.payload = payload


class EventDispatcher:
    """Lightweight asyncio-based pub/sub dispatcher.

    Usage:
      dispatcher = EventDispatcher()
      dispatcher.subscribe('tms.level', callback)
      await dispatcher.publish('tms.level', payload)

    Callbacks may be sync or async functions; they will be scheduled by the
    dispatcher. The dispatcher runs a background delivery task; call
    `start()` before publishing and `stop()` to shutdown cleanly.
    """

    def __init__(self):
        self._subs: Dict[str, List[Callable[[Event], Any]]] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._task: asyncio.Task = None
        self._running = False

    def subscribe(self, topic: str, callback: Callable[[Event], Any]):
        self._subs.setdefault(topic, []).append(callback)

    def unsubscribe(self, topic: str, callback: Callable[[Event], Any]):
        if topic in self._subs:
            try:
                self._subs[topic].remove(callback)
            except ValueError:
                pass

    async def publish(self, topic: str, payload: Any = None):
        await self._queue.put(Event(topic, payload))

    async def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None

    async def _run(self):
        try:
            while self._running:
                event: Event = await self._queue.get()
                callbacks = self._subs.get(event.topic, []) + self._subs.get("*", [])
                for cb in callbacks:
                    try:
                        if asyncio.iscoroutinefunction(cb):
                            asyncio.create_task(cb(event))
                        else:
                            # run sync callback in default loop executor
                            loop = asyncio.get_running_loop()
                            loop.run_in_executor(None, cb, event)
                    except Exception:
                        # swallow per-callback exceptions; callers can log
                        pass
        except asyncio.CancelledError:
            return
