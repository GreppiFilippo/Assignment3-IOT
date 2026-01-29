import asyncio
from services.event_dispatcher import EventDispatcher, Event
from services.mqtt_service import MQTTService
from services.serial_service import SerialService
from services.http_service import HttpService
from models.schemas import ModeRequest, ValveRequest, StatusResponse, Mode, SystemState, LevelReading
from typing import Dict, Any, Optional
from datetime import datetime
from collections import deque
from utils.logger import get_logger
from .base_controller import BaseController
from config import (
    L1_THRESHOLD,
    L2_THRESHOLD,
    T1_DURATION,
    T2_TIMEOUT,
    MAX_READINGS
)

logger = get_logger(__name__)


class SystemController(BaseController):
    """
    System controller implementing business logic for Smart Tank Monitoring.
    
    Configures MQTT, Serial, and HTTP services with specific handlers
    for water level monitoring and valve control.
    """

    def __init__(
        self,
        mqtt_service: MQTTService,
        serial_service: SerialService,
        http_service: HttpService,
        event_dispatcher: EventDispatcher
    ):
        """
        Initialize system controller with specific services.
        
        Args:
            mqtt_service: MQTT service for receiving water level data
            serial_service: Serial service for communicating with WCS
            http_service: HTTP service for REST API
            event_dispatcher: Event dispatcher for inter-service communication
        """
        # Store service references for direct access
        self._mqtt_service = mqtt_service
        self._serial_service = serial_service
        self._http_service = http_service
        
        # State variables
        self._mode: Mode = Mode.AUTOMATIC
        self._state: SystemState = SystemState.AUTOMATIC
        self._valve_opening: float = 0.0
        self._pending_valve_opening: Optional[float] = None
        self._current_level: Optional[float] = None
        self._last_reading_time: Optional[datetime] = None
        self._level_readings: deque[LevelReading] = deque(maxlen=MAX_READINGS)
        
        # Timing control
        self._l1_exceeded_time: Optional[datetime] = None
        self._watchdog_task: Optional[asyncio.Task] = None
        
        # Configure service handlers BEFORE calling super().__init__
        self._configure_services(mqtt_service, serial_service, http_service, event_dispatcher)
        
        # Initialize base controller with services list
        super().__init__(
            services=[mqtt_service, serial_service, http_service],
            event_dispatcher=event_dispatcher
        )
    
    def _configure_services(
        self,
        mqtt: MQTTService,
        serial: SerialService,
        http: HttpService,
        dispatcher: EventDispatcher
    ) -> None:
        """
        Configure all services with handlers.
        
        This method wires up the controller's business logic
        to the infrastructure services using builder pattern.
        """
        # Configure MQTT handlers
        mqtt.register_handler("level", self._on_water_level)
        
        # Configure HTTP endpoints (builder pattern)
        (http
            .register_endpoint("GET", "/api/status", self._get_status)
            .register_endpoint("GET", "/api/readings", self._get_readings)
            .register_endpoint("POST", "/api/mode", self._set_mode)
            .register_endpoint("POST", "/api/valve", self._set_valve)
            .register_endpoint("GET", "/api/health", self._health_check)
        )
        
        # Configure event bus subscriptions
        dispatcher.subscribe("serial_data", self._on_serial_data)
        
        logger.info("SystemController services configured")
    
    # -------------------- Lifecycle Hooks --------------------
    
    async def _on_start(self) -> None:
        """Start watchdog when controller starts."""
        self._watchdog_task = asyncio.create_task(self._watchdog())
        logger.info("SystemController watchdog started")
    
    async def _on_stop(self) -> None:
        """Stop watchdog when controller stops."""
        if self._watchdog_task:
            self._watchdog_task.cancel()
            await asyncio.gather(self._watchdog_task, return_exceptions=True)
        logger.info("SystemController watchdog stopped")
    
    # -------------------- MQTT Handlers --------------------
    
    def _on_water_level(self, level: float) -> None:
        """Handle incoming water level data from TMS."""
        logger.info(f"Received water level: {level} cm")
        
        self._current_level = level
        self._last_reading_time = datetime.now()
        
        # Store reading
        reading = LevelReading(water_level=level, timestamp=self._last_reading_time)
        self._level_readings.append(reading)
        
        # If we were UNCONNECTED, restore to normal mode
        if self._state == SystemState.UNCONNECTED:
            self._state = SystemState.MANUAL if self._mode == Mode.MANUAL else SystemState.AUTOMATIC
            logger.info(f"Connection restored, state now: {self._state}")
            asyncio.create_task(self._send_mode_to_wcs())
        
        # Process level only in AUTOMATIC mode
        if self._mode == Mode.AUTOMATIC:
            self._process_water_level(level)
    
    def _process_water_level(self, level: float) -> None:
        """Process water level according to AUTOMATIC mode logic."""
        
        # Critical level L2: immediately open valve at 100%
        if level >= L2_THRESHOLD:
            logger.warning(f"Water level {level} >= L2 ({L2_THRESHOLD}), opening valve 100%")
            self._l1_exceeded_time = None  # Reset L1 timer
            self._set_valve_opening(100.0)
        
        # High level L1: open valve at 50% after T1 duration
        elif level >= L1_THRESHOLD:
            if self._l1_exceeded_time is None:
                self._l1_exceeded_time = datetime.now()
                logger.info(f"Water level {level} >= L1 ({L1_THRESHOLD}), starting timer T1")
            else:
                elapsed = (datetime.now() - self._l1_exceeded_time).total_seconds()
                if elapsed >= T1_DURATION and self._valve_opening < 50.0:
                    logger.warning(f"Water level above L1 for {elapsed}s >= T1, opening valve 50%")
                    self._set_valve_opening(50.0)
        
        # Normal level: close valve if it was open
        else:
            self._l1_exceeded_time = None  # Reset timer
            if self._valve_opening > 0.0:
                logger.info(f"Water level {level} below L1, closing valve")
                self._set_valve_opening(0.0)
    
    def _set_valve_opening(self, opening: float) -> None:
        """Set valve opening and send command to WCS via serial."""
        logger.info(f"Setting valve opening to {opening}%")
        
        # Try to send command to WCS
        success = self._serial_service.send_message({"valve": opening})
        
        if success:
            # Mark as pending until WCS confirms
            self._pending_valve_opening = opening
            logger.debug(f"Valve command sent, waiting for confirmation")
        else:
            logger.error(f"Failed to send valve command to WCS")
    
    async def _send_mode_to_wcs(self) -> None:
        """Send current mode to WCS for LCD display."""
        self._serial_service.send_message({"mode": self._state.value})
    
    # -------------------- Event Bus Handlers --------------------
    
    async def _on_serial_data(self, event: Event) -> None:
        """Handle incoming data from WCS via serial."""
        data = event.payload
        
        # Handle valve confirmation from WCS
        if "valve" in data:
            confirmed_opening = float(data["valve"])
            if self._pending_valve_opening is not None and abs(confirmed_opening - self._pending_valve_opening) < 0.1:
                self._valve_opening = confirmed_opening
                self._pending_valve_opening = None
                logger.info(f"Valve opening confirmed at {confirmed_opening}%")
            else:
                # WCS reports different value (e.g., manual pot adjustment)
                self._valve_opening = confirmed_opening
                logger.debug(f"Valve opening updated from WCS: {confirmed_opening}%")
        
        # Handle button press
        if "button" in data and data["button"] == 1:
            await self._on_button_pressed()
        
        # Handle potentiometer value
        if "potentiometer" in data:
            value = float(data["potentiometer"])
            await self._on_potentiometer_value(value)
    
    async def _on_button_pressed(self) -> None:
        """Handle button press from WCS to toggle MANUAL mode."""
        if self._mode == Mode.AUTOMATIC:
            self._mode = Mode.MANUAL
            self._state = SystemState.MANUAL
            logger.info("Switched to MANUAL mode")
        else:
            self._mode = Mode.AUTOMATIC
            self._state = SystemState.AUTOMATIC
            logger.info("Switched to AUTOMATIC mode")
        
        await self._send_mode_to_wcs()
    
    async def _on_potentiometer_value(self, value: float) -> None:
        """Handle potentiometer change from WCS (in MANUAL mode)."""
        if self._mode == Mode.MANUAL:
            self._set_valve_opening(value)
    
    # -------------------- HTTP Handlers --------------------
    
    async def _get_status(self) -> StatusResponse:
        """Get current system status."""
        # Check serial connection status
        serial_connected = self._serial_service.is_connected()
        
        # Use pending valve if not yet confirmed
        valve_value = self._pending_valve_opening if self._pending_valve_opening is not None else self._valve_opening
        
        # Determine state: NOT_AVAILABLE if serial disconnected
        state = SystemState.NOT_AVAILABLE if not serial_connected else self._state
        
        return StatusResponse(
            state=state,
            mode=self._mode,
            valve_opening=valve_value,
            water_level=self._current_level,
            timestamp=self._last_reading_time
        )
    
    async def _get_readings(self, limit: int = 60) -> list[Dict[str, Any]]:
        """
        Get latest water level readings.
        
        Args:
            limit: Number of readings to return (default: 60, max: all stored)
        
        Returns:
            List of readings with water_level and timestamp
        """
        # Clamp limit to valid range
        limit = max(1, min(limit, len(self._level_readings)))
        
        readings = list(self._level_readings)[-limit:]
        return [
            {
                "ts": r.timestamp.isoformat(),
                "value": r.water_level
            }
            for r in readings
        ]
    
    async def _set_mode(self, req: ModeRequest) -> Dict[str, str]:
        """Set system mode (AUTOMATIC/MANUAL) from dashboard."""
        logger.info(f"Dashboard requested mode change to {req.mode}")
        
        self._mode = req.mode
        self._state = SystemState.MANUAL if req.mode == Mode.MANUAL else SystemState.AUTOMATIC
        
        # Reset automatic mode state
        if self._mode == Mode.AUTOMATIC:
            self._l1_exceeded_time = None
        
        await self._send_mode_to_wcs()
        return {"result": "ok"}
    
    async def _set_valve(self, req: ValveRequest) -> Dict[str, str]:
        """Set valve opening (MANUAL mode only) from dashboard."""
        if self._mode != Mode.MANUAL:
            logger.warning("Valve control attempted while not in MANUAL mode")
            return {"result": "error", "message": "Not in MANUAL mode"}
        
        logger.info(f"Dashboard set valve to {req.opening}%")
        self._set_valve_opening(req.opening)
        return {"result": "ok"}
    
    async def _health_check(self) -> Dict[str, str]:
        """Health check endpoint."""
        return {"status": "alive"}
     
    # -------------------- Watchdog --------------------
    
    async def _watchdog(self) -> None:
        """Monitor TMS connection timeout (T2)."""
        while True:
            await asyncio.sleep(1.0)
            
            if self._last_reading_time is not None:
                elapsed = (datetime.now() - self._last_reading_time).total_seconds()
                
                if elapsed > T2_TIMEOUT and self._state != SystemState.UNCONNECTED:
                    logger.error(f"No data from TMS for {elapsed}s > T2, entering UNCONNECTED state")
                    self._state = SystemState.UNCONNECTED
                    await self._send_mode_to_wcs()
