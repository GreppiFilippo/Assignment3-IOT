import asyncio
from typing import Any, Optional

class SerialConn:
    """Minimal serial connection wrapper skeleton.

    Replace internals with `pyserial-asyncio` or other serial library.
    The class exposes `start()`/`stop()` and publishes incoming lines to an
    `event_bus` via `event_bus.publish(topic, payload)`.
    """

    def __init__(self, port: str, baud: int = 115200, event_bus: Optional[Any] = None):
        self.port = port
        self.baud = baud
        self.event_bus = event_bus
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._read_loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None

    async def send_line(self, line: str):
        """Send a line to the serial device (append newline)."""
        # TODO: implement using pyserial-asyncio write
        await asyncio.sleep(0)

    async def _read_loop(self):
        """Loop reading lines from serial and publishing to event_bus."""
        try:
            # TODO: open serial port with asyncio-compatible API
            while self._running:
                # placeholder: simulate incoming data
                await asyncio.sleep(1)
                sample = "WCS:sample_line"
                if self.event_bus:
                    await self.event_bus.publish("wcs.line", sample)
        except asyncio.CancelledError:
            return
