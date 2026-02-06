import asyncio
import json
import serial
import time
from typing import Optional, Dict, Any, Callable

from services.event_bus import EventBus
from .base_service import BaseService
from utils.logger import get_logger

logger = get_logger(__name__)


class SerialService(BaseService):
    """
    Serial infrastructure adapter.
    Handles hardware communication and translates between Serial data and Event Bus topics.
    """

    def __init__(
        self,
        port: str,
        baudrate: int,
        event_bus: EventBus,
        send_interval: float = 0.5,
    ):
        super().__init__("serial_service", event_bus)

        self.port = port
        self.baudrate = baudrate
        self._send_interval = send_interval

        # Serial internals
        self._serial: Optional[serial.Serial] = None
        self._read_buffer = ""
        self._last_send_time = 0.0

        # -------------------------
        # SERIAL STATE (IL "COSA")
        # -------------------------
        self._state: Dict[str, Any] = {
            "mode": "UNCONNECTED",
            "valve": 0.0,
        }

        # -------------------------
        # EVENT → STATE MAPPING
        # -------------------------
        self._event_field_map: Dict[str, Callable[[Any], Any]] = {
            "mode": lambda v: v.value if hasattr(v, "value") else str(v),
            "valve": float,
        }

        # -------------------------
        # SERIAL → BUS MAPPING
        # -------------------------
        self._pub_topics: Dict[str, str] = {
            "pot": "pot",
            "btn": "btn",
        }

    # =========================================================================
    # LIFECYCLE
    # =========================================================================

    async def setup(self):
        """Open the serial port using a thread executor to avoid blocking."""
        try:
            loop = asyncio.get_running_loop()
            self._serial = await loop.run_in_executor(
                None,
                lambda: serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=0.1,
                ),
            )
            logger.info(f"[{self.name}] Port {self.port} opened.")
        except Exception as e:
            logger.error(f"[{self.name}] Failed to open port {self.port}: {e}")
            self._serial = None

    async def run(self):
        """Main loop managing periodic sending and continuous reading."""
        while self._running:
            if self._serial is None or not self._serial.is_open:
                await asyncio.sleep(2)
                continue

            try:
                await self._read_serial_data()

                now = time.monotonic()
                if now - self._last_send_time >= self._send_interval:
                    await self._write_serial_data(self._state)
                    self._last_send_time = now

            except Exception as e:
                logger.error(f"[{self.name}] Runtime error: {e}")
                self._serial = None

            await asyncio.sleep(0.01)

    async def cleanup(self):
        if self._serial:
            self._serial.close()
            logger.info(f"[{self.name}] Serial port closed.")

    # =========================================================================
    # GENERIC STATE UPDATE (IL "COME")
    # =========================================================================

    def on_event(self, field: str, value: Any):
        if field not in self._event_field_map:
            logger.warning(f"[{self.name}] Unknown state field: {field}")
            return

        transform = self._event_field_map[field]
        self._state[field] = transform(value)

        logger.debug(
            f"[{self.name}] State updated: {field}={self._state[field]}"
        )

    # =========================================================================
    # ADAPTERS (SOTTILI, STUPIDI, STABILI)
    # =========================================================================

    def on_mode_change(self, mode: Any):
        self.on_event("mode", mode)

    def on_valve_command(self, opening: float):
        self.on_event("valve", opening)

    # =========================================================================
    # SERIAL IO
    # =========================================================================

    async def _read_serial_data(self):
        if self._serial is None:
            return

        loop = asyncio.get_running_loop()
        ser = self._serial

        try:
            waiting = await loop.run_in_executor(None, lambda: ser.in_waiting)
            if waiting > 0:
                raw = await loop.run_in_executor(None, lambda: ser.read(waiting))
                self._read_buffer += raw.decode("utf-8", errors="ignore")

                while "\n" in self._read_buffer:
                    line, self._read_buffer = self._read_buffer.split("\n", 1)
                    await self._process_incoming_line(line.strip())

        except Exception as e:
            logger.error(f"[{self.name}] Serial read error: {e}")
            self._serial = None

    async def _process_incoming_line(self, line: str):
        if not line:
            return

        try:
            data = json.loads(line)
            for key, value in data.items():
                if key in self._pub_topics:
                    topic = self._pub_topics[key]
                    self.bus.publish(key, **{topic: value})
                    logger.debug(
                        f"[{self.name}] Published: {key} → {topic}={value}"
                    )

        except json.JSONDecodeError:
            logger.warning(f"[{self.name}] Invalid JSON: {line}")

    async def _write_serial_data(self, data: dict):
        if self._serial is None:
            return

        try:
            loop = asyncio.get_running_loop()
            payload = (json.dumps(data) + "\n").encode("utf-8")
            await loop.run_in_executor(None, self._serial.write, payload)
            await loop.run_in_executor(None, self._serial.flush)

            logger.debug(f"[{self.name}] Sent: {data}")

        except Exception as e:
            logger.error(f"[{self.name}] Serial write error: {e}")
            self._serial = None