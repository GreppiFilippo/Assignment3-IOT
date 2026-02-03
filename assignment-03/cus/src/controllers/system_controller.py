import asyncio
import json
from datetime import datetime
from pydantic import ValidationError
from services.event_dispatcher import EventDispatcher
from services.mqtt_service import MQTTService
from services.serial_service import SerialService
from services.http_service import HttpService
from models.system_model import SystemModel
from models.schemas import LevelReading, TankLevelPayload
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
        model: SystemModel,
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
        # Initialize base model
        self._model = model

        # Store service references for direct access
        self._mqtt_service = mqtt_service

        self._mqtt_service.register_payload_handler(self._on_tank_level)


        self._serial_service = serial_service

        self._serial_service.register_handler(self.msg_from_serial)
        self._http_service = http_service
        
        # Initialize base controller with services list
        super().__init__(
            services=[mqtt_service, serial_service, http_service],
            event_dispatcher=event_dispatcher
        )

    async def _on_start(self) -> None:
        pass
    async def _on_stop(self) -> None:
        pass
    

    def _on_tank_level(self, payload: str) -> None:
        """
        Handle incoming water level data from MQTT.
        Content-agnostic: handles both JSON and plain text formats.
        
        Args:
            payload: Raw MQTT payload string
        """
        try:
            # Try JSON format first: {"level": 45.23, "timestamp": 1234567890}
            data = json.loads(payload)
            validated = TankLevelPayload(**data)
            logger.info(f"Received water level: {validated.level}, timestamp: {validated.to_datetime()}")
            self._model.add_level_reading(
                LevelReading(water_level=validated.level, timestamp=validated.to_datetime())
            )
            
        except json.JSONDecodeError:
            # Plain text format: just the level value
            try:
                level = float(payload.strip())
                timestamp = datetime.now()
                logger.info(f"Received water level (plain): {level}, using current time")
                self._model.add_level_reading(
                    LevelReading(water_level=level, timestamp=timestamp)
                )
            except ValueError:
                logger.error(f"Invalid plain text level: {payload}")
                
        except ValidationError as e:
            logger.error(f"Invalid JSON structure: {e.errors()}")
        except Exception as e:
            logger.exception(f"Failed to process tank level: {e}")

    def msg_from_serial(self, data: dict) -> None:
        """
        Handle incoming messages from Serial service.
        
        Args:
            data: Parsed data dictionary from serial input
        """
        logger.debug(f"Processing serial data: {data}")
        
