import asyncio
import json
import serial
import time
from typing import Optional, Dict, Callable, Any

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
        # Mapping: { "serial_key": "bus_topic" } per publishing multiplo
        self._pub_topics: Dict[str, str] = {}
        # Mapping: { "bus_topic": callback } per subscription personalizzate
        self._sub_handlers: Dict[str, Callable] = {}

    def configure_messaging(self, pub_topics: Optional[Dict[str, str]] = None, sub_topics: Optional[Dict[str, str]] = None):
        """
        Configure multi-topic pub/sub wiring.
        
        :param pub_topics: Dict mapping serial data keys to bus topics
                          Example: {"POT_VAL": "sensor.level", "TEMP": "sensor.temperature"}
        :param sub_topics: Dict mapping bus topics to serial command keys
                          Example: {"cmd.valve": "VALVE", "cmd.alarm": "ALARM"}
        """
        if pub_topics:
            self._pub_topics = pub_topics
            logger.info(f"[{self.name}] Will publish: {pub_topics}")
        
        if sub_topics:
            for bus_topic, serial_key in sub_topics.items():
                # Crea callback specifica per ogni topic
                callback = self._make_subscription_handler(serial_key)
                self.bus.subscribe(bus_topic, callback)
                self._sub_handlers[bus_topic] = callback
                logger.info(f"[{self.name}] Subscribed to: {bus_topic} → Serial key: {serial_key}")

    def _make_subscription_handler(self, serial_key: str):
        """Factory per creare callback specifiche per ogni topic."""
        def handler(**kwargs):
            # Salva i dati con la chiave serial corretta
            self._last_state_received[serial_key] = kwargs
            logger.debug(f"[{self.name}] Received on bus → {serial_key}: {kwargs}")
        return handler

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
        if not line or not self._pub_topics: return
        try:
            data = json.loads(line)
            
            # Pubblica su topic multipli in base ai dati ricevuti
            for serial_key, bus_topic in self._pub_topics.items():
                if serial_key in data:
                    # Extract value and publish with the FSM-expected parameter name
                    value = data[serial_key]
                    if bus_topic == "sensor.level":
                        # FSM expects: sensor.level(level=X)
                        self.bus.publish(bus_topic, level=value)
                    else:
                        # Generic pass-through for other topics
                        self.bus.publish(bus_topic, **{serial_key: value})
                    logger.debug(f"[{self.name}] Published {serial_key} → {bus_topic}: {value}")
                    
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