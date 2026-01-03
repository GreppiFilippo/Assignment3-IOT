from utils.logger import get_logger
import asyncio
from typing import Any, Optional

logger = get_logger(__name__)


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
        logger.info(f"SerialConn created for port {port} @ {baud} baud")

    async def start(self):
        logger.info(f"Starting SerialConn on {self.port}")
        self._running = True
        self._task = asyncio.create_task(self._read_loop())

    async def stop(self):
        logger.info(f"Stopping SerialConn on {self.port}")
        self._running = False
        if self._task:
            self._task.cancel()
            await asyncio.gather(self._task, return_exceptions=True)
            self._task = None

    async def send_line(self, line: str):
        """Send a line to the serial device (append newline)."""
        logger.debug(f"Sending to serial: {line}")
        # TODO: implement using pyserial-asyncio write
        await asyncio.sleep(0)

    async def _read_loop(self):
        """Loop reading lines from serial and publishing to event_bus."""
        try:
            logger.debug("Serial read loop started")
            # TODO: open serial port with asyncio-compatible API
            while self._running:
                # placeholder: simulate incoming data
                await asyncio.sleep(1)
                sample = "WCS:sample_line"
                logger.debug(f"Serial received: {sample}")
                if self.event_bus:
                    await self.event_bus.publish("wcs.line", sample)
        except asyncio.CancelledError:
            logger.debug("Serial read loop cancelled")
            return
