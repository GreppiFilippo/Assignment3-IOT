import asyncio
import json
import serial
from serial.serialutil import SerialException
from typing import Callable, Optional
from .base_service import BaseService
from .event_dispatcher import EventDispatcher
from utils.logger import get_logger

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
        timeout: float = 0.1
    ):
        """
        Initialize serial service.
        
        :param self: The instance
        :param event_dispatcher: Event dispatcher for inter-service communication
        :type event_dispatcher: EventDispatcher
        :param port: Serial port path (e.g., "COM3" on Windows, "/dev/ttyUSB0" on Linux)
        :type port: str
        :param baudrate: Serial communication speed (typically 9600)
        :type baudrate: int
        :param timeout: Read timeout in seconds (default: 0.1 for non-blocking)
        :type timeout: float
        """
        super().__init__("serial_service", event_dispatcher)
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None
        self._raw_handlers: list[Callable[[str], None]] = []
        self._read_buffer = ""
        logger.info(f"{self.name} initialized for port {port} at {baudrate} baud")
    
    async def run(self) -> None:
        """Run serial service with read loop."""
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
            # Run read loop
            while self._running:
                await self._read_loop()
                await asyncio.sleep(0.01)  # Small delay to prevent CPU spinning
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
            # Read available bytes without blocking
            if self._serial.in_waiting > 0:
                data = self._serial.read(self._serial.in_waiting)
                self._read_buffer += data.decode('utf-8', errors='ignore')
                
                # Process complete lines
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
            
            # Publish raw data to event bus - controller decides what to do
            await self.event_dispatcher.publish("serial_data", data)
            
        except json.JSONDecodeError:
            logger.warning(f"{self.name} received invalid JSON: {message}")
        except Exception as e:
            logger.exception(f"{self.name} error processing message: {e}")
    
    async def send_message(self, data: dict) -> bool:
        """
        Send JSON message to WCS via serial.
        
        Args:
            data: Dictionary to send as JSON (will be newline-terminated)
        
        Returns:
            True if message was sent successfully, False otherwise
        
        Example:
            serial.send_message({"valve": 50.0})
            serial.send_message({"mode": "AUTOMATIC"})
        """
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
    
    def is_connected(self) -> bool:
        """Check if serial port is connected and open."""
        return self._serial is not None and self._serial.is_open
    
    def register_handler(self, callback) -> 'SerialService':
        """
        Register a callback to handle incoming serial data.
        
        Args:
            callback: Function to call with incoming data dictionary
        
        Returns:
            Self for chaining
        
        Example:
            def handle_serial_data(data):
                print("Received from serial:", data)
            
            serial.register_handler(handle_serial_data)
        """
        self._raw_handlers.append(callback)
        logger.info(f"{self.name} registered serial handler")
        return self
