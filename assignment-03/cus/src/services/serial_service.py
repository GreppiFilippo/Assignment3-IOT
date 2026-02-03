import asyncio
import json
import serial
from serial.serialutil import SerialException
from typing import Callable, Optional
from .base_service import BaseService
from .event_dispatcher import EventDispatcher
from .event_bus import EventBus
from utils.logger import get_logger
import time

logger = get_logger(__name__)


class SerialService(BaseService):
    """
    Serial communication service for interacting with WCS (Arduino).
    """

    def __init__(
        self, 
        event_dispatcher: EventDispatcher, 
        port: str, 
        baudrate: int,
        timeout: float = 0.1,
        send_interval: float = 0.5  # intervallo per inviare self.json
    ):
        super().__init__("serial_service", event_dispatcher)
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None
        self._raw_handlers: list[Callable[[str], None]] = []
        self._read_buffer = ""
        self.json: dict = {}
        self._send_interval = send_interval
        self._last_send = 0.0
        logger.info(f"{self.name} initialized for port {port} at {baudrate} baud")
    
    async def run(self) -> None:
        """Run serial service with read loop and periodic send of self.json."""
        logger.info(f"{self.name} attempting to open port {self.port}")
        
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            logger.info(f"{self.name} successfully opened {self.port}")
        except SerialException as e:
            logger.error(f"{self.name} failed to open port {self.port}: {e}")
            return

        try:
            while self._running:
                await self._read_loop()
                await self._send_if_needed()
                await asyncio.sleep(0.01)  # small delay to avoid CPU spinning
        except Exception as e:
            logger.exception(f"{self.name} error in run loop: {e}")
        finally:
            if self._serial and self._serial.is_open:
                self._serial.close()
                logger.info(f"{self.name} closed port {self.port}")
    
    async def _read_loop(self) -> None:
        """Read data from serial port and publish to event bus."""
        if not self._serial or not self._serial.is_open:
            return
        try:
            if self._serial.in_waiting > 0:
                data = self._serial.read(self._serial.in_waiting)
                self._read_buffer += data.decode('utf-8', errors='ignore')
                
                while '\n' in self._read_buffer:
                    line, self._read_buffer = self._read_buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        await self._process_incoming_message(line)
        except SerialException as e:
            logger.error(f"{self.name} read error: {e}")
        except Exception as e:
            logger.exception(f"{self.name} unexpected error in read loop: {e}")
    
    async def _process_incoming_message(self, message: str) -> None:
        """Parse and publish incoming message to event bus."""
        try:
            data = json.loads(message)
            logger.debug(f"{self.name} received: {data}")
            
            for topic, event_data in data.items():
                if not isinstance(event_data, dict):
                    logger.warning(f"Skipping topic {topic}: payload not dict")
                    continue

                asyncio.run_coroutine_threadsafe(
                    EventBus.publish(topic, **event_data),
                    self._loop
                )
        except json.JSONDecodeError:
            logger.warning(f"{self.name} received invalid JSON: {message}")
        except Exception as e:
            logger.exception(f"{self.name} error processing message: {e}")
    
    async def send_message(self, data: dict) -> bool:
        """Send JSON message to WCS via serial."""
        if not self._serial or not self._serial.is_open:
            logger.warning(f"{self.name} cannot send message, serial port not open")
            return False
        
        try:
            loop = asyncio.get_running_loop()
            message = json.dumps(data) + '\n'
            await loop.run_in_executor(None, self._serial.write, message.encode('utf-8'))
            await loop.run_in_executor(None, self._serial.flush)
            logger.debug(f"{self.name} sent: {data}")
            return True
        except SerialException as e:
            logger.error(f"{self.name} write error: {e}")
            return False
        except Exception as e:
            logger.exception(f"{self.name} error sending message: {e}")
            return False
    
    async def _send_if_needed(self) -> None:
        """Send self.json every send_interval, anche se è vuoto."""
        now = time.monotonic()
        if now - self._last_send < self._send_interval:
            return

        # Invia sempre, anche se dict è vuoto
        await self.send_message(self.json)
        self._last_send = now

    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    # --- helper per aggiornare lo stato ---
    def store_new_mode(self, mode: str) -> None:
        self.json["mode"] = mode

    def store_new_opening(self, opening: float) -> None:
        self.json["valve_opening"] = opening
