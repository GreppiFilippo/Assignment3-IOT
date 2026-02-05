import asyncio
import json
import serial
import time
from typing import Optional, List

from services.event_bus import EventBus
from .base_service import BaseService
from utils.logger import get_logger

logger = get_logger(__name__)

class SerialService(BaseService):
    """
    Serial infrastructure adapter.
    Handles hardware communication and translates between Serial data and Event Bus topics.
    """

    def __init__(self, port: str, baudrate: int, event_bus: EventBus, send_interval: float = 0.5):
        super().__init__("serial_service", event_bus)
        self.port = port
        self.baudrate = baudrate
        self._send_interval = send_interval
        
        # Internal state
        self._serial: Optional[serial.Serial] = None
        self._read_buffer = ""
        self._last_state_received: dict = {}
        self._last_send_time = 0.0
        
        # Messaging configuration (set via configure_messaging)
        self._pub_topic: Optional[str] = None

    def configure_messaging(self, pub_topic: str, sub_topics: List[str]):
        """
        Configure the pub/sub wiring from the main entry point.
        
        :param pub_topic: The topic where serial data will be published.
        :param sub_topics: List of topics this service should listen to.
        """
        self._pub_topic = pub_topic
        for topic in sub_topics:
            self.bus.subscribe(topic, self._on_bus_message)
            logger.info(f"[{self.name}] Subscribed to topic: {topic}")

    def _on_bus_message(self, **kwargs):
        """Callback for incoming messages from the Event Bus."""
        # Update the local state to be sent to hardware on next tick
        self._last_state_received.update(kwargs)

    async def setup(self):
        """Open the serial port using a thread executor to avoid blocking."""
        try:
            loop = asyncio.get_running_loop()
            self._serial = await loop.run_in_executor(
                None, 
                lambda: serial.Serial(port=self.port, baudrate=self.baudrate, timeout=0.1)
            )
            logger.info(f"[{self.name}] Port {self.port} opened successfully.")
        except Exception as e:
            logger.error(f"[{self.name}] Failed to open port {self.port}: {e}")
            self._serial = None

    async def run(self):
        """Main loop managing periodic sending and continuous reading."""
        while self._running:
            if self._serial is None or not self._serial.is_open:
                await asyncio.sleep(2)  # Wait before retry
                continue

            try:
                # 1. Read from Hardware
                await self._read_serial_data()

                # 2. Periodic Write to Hardware (Heartbeat/State sync)
                now = time.monotonic()
                if now - self._last_send_time >= self._send_interval:
                    await self._write_serial_data(self._last_state_received)
                    self._last_send_time = now

            except Exception as e:
                logger.error(f"[{self.name}] Error in run loop: {e}")
                self._serial = None  # Force reconnection logic

            await asyncio.sleep(0.01)

    async def _read_serial_data(self):
        """Non-blocking read from the serial port."""
        if self._serial is None: return
        
        loop = asyncio.get_running_loop()
        ser = self._serial # Local reference for thread-safety
        
        try:
            waiting = await loop.run_in_executor(None, lambda: ser.in_waiting)
            if waiting > 0:
                raw = await loop.run_in_executor(None, lambda: ser.read(waiting))
                self._read_buffer += raw.decode('utf-8', errors='ignore')
                
                while '\n' in self._read_buffer:
                    line, self._read_buffer = self._read_buffer.split('\n', 1)
                    await self._process_incoming_line(line.strip())
        except Exception as e:
            logger.error(f"[{self.name}] Read error: {e}")
            self._serial = None

    async def _process_incoming_line(self, line: str):
        """Parse JSON from hardware and publish to the Event Bus."""
        if not line or not self._pub_topic: return
        try:
            data = json.loads(line)
            # Publish using the topic injected from main
            self.bus.publish(self._pub_topic, **data)
        except json.JSONDecodeError:
            logger.warning(f"[{self.name}] Invalid JSON received: {line}")

    async def _write_serial_data(self, data: dict):
        """Send the current state as JSON to the hardware."""
        if self._serial is None: return
        try:
            loop = asyncio.get_running_loop()
            ser = self._serial
            payload = (json.dumps(data) + '\n').encode('utf-8')
            await loop.run_in_executor(None, lambda: ser.write(payload))
            await loop.run_in_executor(None, ser.flush)
        except Exception as e:
            logger.error(f"[{self.name}] Write error: {e}")
            self._serial = None

    async def cleanup(self):
        """Ensure the serial port is closed on shutdown."""
        if self._serial:
            self._serial.close()
            logger.info(f"[{self.name}] Serial port closed.")