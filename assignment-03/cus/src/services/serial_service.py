import asyncio
import json
import serial
from serial.serialutil import SerialException
from typing import Optional
from .base_service import BaseService
from .event_bus import EventBus
from utils.logger import get_logger

logger = get_logger(__name__)


class SerialService(BaseService):
    """
    Serial communication service for interacting with WCS (Arduino).
    """

    def __init__(
        self, 
        port: str, 
        baudrate: int,
        timeout: float = 0.1
    ):
        """
        Initialize serial service.
        
        :param port: Serial port path (e.g., "COM3" on Windows, "/dev/ttyUSB0" on Linux)
        :type port: str
        :param baudrate: Serial communication speed (typically 9600)
        :type baudrate: int
        :param timeout: Read timeout in seconds (default: 0.1 for non-blocking)
        :type timeout: float
        """
        super().__init__("serial_service", None)  # No event_dispatcher needed
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None
        self._read_buffer = ""
        
        logger.info(f"{self.name} initialized for port {port} at {baudrate} baud")
        
        # Subscribe to command events
        EventBus.subscribe("valve.set", self._on_valve_command)
        EventBus.subscribe("alarm.set", self._on_alarm_command)
        logger.info(f"{self.name} subscribed to command events")
    
    async def run(self) -> None:
        """Run serial service with auto-reconnect."""
        logger.info(f"{self.name} attempting to open port {self.port}")
        
        retry_interval = 5  # seconds between reconnection attempts
        
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            logger.info(f"{self.name} successfully opened {self.port}")
        except SerialException as e:
            logger.error(f"{self.name} failed to open port {self.port}: {e}")
            logger.info(f"{self.name} will retry connection every {retry_interval}s")
        
        try:
            # Run read loop with auto-reconnect
            while self._running:
                # Try to reconnect if not connected
                if not self.is_connected():
                    try:
                        logger.info(f"{self.name} attempting to reconnect to {self.port}...")
                        self._serial = serial.Serial(
                            port=self.port,
                            baudrate=self.baudrate,
                            timeout=self.timeout
                        )
                        logger.info(f"{self.name} reconnected successfully")
                    except SerialException as e:
                        logger.debug(f"{self.name} reconnect failed: {e}")
                        # Sleep in small intervals to allow quick shutdown
                        for _ in range(retry_interval * 10):
                            if not self._running:
                                break
                            await asyncio.sleep(0.1)
                        continue
                
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
        """Parse and publish incoming message to event bus as domain events."""
        try:
            data = json.loads(message)
            logger.debug(f"{self.name} received: {data}")
            
            # Publish as domain event "wcs.status" using EventBus
            await EventBus.publish("wcs.status", data=data)
            
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

    async def _on_valve_command(self, position: float) -> None:
        """
        Handle valve command from EventBus.
        
        Args:
            position: Valve position percentage (0-100)
        """
        logger.info(f"{self.name} executing valve command: {position}%")
        await self.send_message({"valve": position})
    
    async def _on_alarm_command(self, active: bool) -> None:
        """
        Handle alarm command from EventBus.
        
        Args:
            active: Alarm state (True=ON, False=OFF)
        """
        logger.info(f"{self.name} executing alarm command: {'ON' if active else 'OFF'}")
        await self.send_message({"alarm": active})
