from ast import List
from models.system_model import SystemModel
from utils.logger import setup_logging, get_logger
import asyncio
from core.system_controller import SystemController
from services.event_dispatcher import EventDispatcher
from services.mqtt_service import MQTTService
from services.serial_service import SerialService
from services.http_service import HttpService
import config
from core.mock_controller import MockController


# Setup logging
setup_logging(log_level=config.LOG_LEVEL, log_file=config.LOG_FILE)
logger = get_logger(__name__)


async def main():
    logger.info("Initializing CUS application")

    model = SystemModel()

    # Create shared dependencies
    event_dispatcher = EventDispatcher()

    # Create services with configuration
    mqtt_service = MQTTService(
        event_dispatcher,
        config.MQTT_BROKER_HOST,
        config.MQTT_BROKER_PORT,
        config.MQTT_TOPIC
    )

    serial_service = SerialService(
        event_dispatcher=event_dispatcher,
        port=config.SERIAL_PORT,
        baudrate=config.SERIAL_BAUDRATE
    )

    http_service = HttpService(
        event_dispatcher,
        host=config.HTTP_HOST,
        port=config.HTTP_PORT
    )

    # Inject dependencies into controller
    # Controller handles its own handler registration
    services = [mqtt_service, serial_service, http_service]

    controller = SystemController(
        model=model,
        event_dispatcher=event_dispatcher,
        mqtt_service=mqtt_service, 
        serial_service=serial_service, 
        http_service=http_service
    )

    try:
        await controller.run()
    except asyncio.CancelledError:
        logger.info("Application cancelled, shutting down...")
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    finally:
        # Ensure clean shutdown of all services
        await controller.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
