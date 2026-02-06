import asyncio
import json
import serial
import time
from enum import Enum
from typing import Optional, Dict, Callable, Any
from functools import partial

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
        self._last_state_to_send: dict = {}
        self._last_send_time = 0.0
        
        # Mapping from serial keys to event bus topics (configurable)
        self._incoming_map: Dict[str, str] = {}  # {"pot": "pot_topic"}
        self._state_keys: list = []  # ["mode", "valve"] - keys to send to hardware
        
    def configure_messaging(self, incoming: Optional[Dict[str, str]] = None, 
                           outgoing_state_keys: Optional[list] = None, 
                           initial_state: Optional[dict] = None):
        """
        Configure serial communication mappings.
        :param incoming: Map of {"serial_key": "bus_topic"} for data from hardware
        :param outgoing_state_keys: List of state keys to send to hardware
        :param initial_state: Initial state dict to send to hardware
        """
        if incoming:
            self._incoming_map = incoming
            logger.info(f"[{self.name}] Incoming map: {incoming}")
        
        if outgoing_state_keys:
            self._state_keys = outgoing_state_keys
            logger.info(f"[{self.name}] State keys to send: {outgoing_state_keys}")
        
        if initial_state:
            self._last_state_to_send = initial_state
            logger.info(f"[{self.name}] Initial state: {initial_state}")
    
    def on_state_change(self, state_key: str, **kwargs):
        """
        Generic callback to update state to send to hardware.
        :param state_key: Key in the state dict
        :param kwargs: Data (if single value, extract it)
        """
        if len(kwargs) == 1:
            self._last_state_to_send[state_key] = list(kwargs.values())[0]
        else:
            self._last_state_to_send[state_key] = kwargs
        logger.debug(f"[{self.name}] State updated: {state_key} = {self._last_state_to_send[state_key]}")
    
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
                    await self._write_serial_data(self._last_state_to_send)
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
        if not line or not self._incoming_map: return
        try:
            data = json.loads(line)
            for key, value in data.items():
                if key in self._incoming_map:
                    bus_topic = self._incoming_map[key]
                    self.bus.publish(bus_topic, **{key: value})
                    logger.debug(f"Published to {bus_topic}: {key}={value}")
        except json.JSONDecodeError:
            logger.warning(f"[{self.name}] Invalid JSON received: {line}")

    def _serialize_value(self, value):
        """Convert value to JSON-serializable format (handles enums, etc.)."""
        if isinstance(value, Enum):
            return value.value
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(v) for v in value]
        return value

    async def _write_serial_data(self, data: dict):
        """Send the current state as JSON to the hardware."""
        if self._serial is None: return
        try:
            loop = asyncio.get_running_loop()
            ser = self._serial
            # Serialize data to handle enums and other non-JSON types
            serializable_data = {k: self._serialize_value(v) for k, v in data.items()}
            payload = (json.dumps(serializable_data) + '\n').encode('utf-8')
            print(f"[{self.name}] 📤 Sending to WCS: {serializable_data}")
            logger.debug(f"[{self.name}] Sending to WCS: {serializable_data}")
            await loop.run_in_executor(None, lambda: ser.write(payload))
            await loop.run_in_executor(None, ser.flush)
        except Exception as e:
            print(f"[{self.name}] ❌ Write error: {e}")
            logger.error(f"[{self.name}] Write error: {e}")
            self._serial = None

    async def cleanup(self):
        """Ensure the serial port is closed on shutdown."""
        if self._serial:
            self._serial.close()
            logger.info(f"[{self.name}] Serial port closed.")
