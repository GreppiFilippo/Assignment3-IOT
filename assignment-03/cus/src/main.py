from models.system_model import SystemModel
from utils.logger import setup_logging, get_logger
import asyncio
from controllers.system_controller import SystemController
from services.mqtt_service import MQTTService
from services.serial_service import SerialService
from services.http_service import HttpService
import config
from services.event_bus import EventBus
from controllers.orchestrator import Orchestrator

# Setup logging
setup_logging(log_level=config.LOG_LEVEL, log_file=config.LOG_FILE)
logger = get_logger(__name__)

status = 0
async def main():
    logger.info("Initializing CUS application with PyPubSub EventBus")
    event_bus = EventBus()
    model = SystemModel()

    
    # Create services (no event_dispatcher needed - using EventBus)
    mqtt_service = MQTTService(
        broker=config.MQTT_BROKER_HOST,
        port=config.MQTT_BROKER_PORT
    )

    serial_service = SerialService(
        port=config.SERIAL_PORT,
        baudrate=config.SERIAL_BAUDRATE
    )

    http_service = HttpService(
        host=config.HTTP_HOST,
        port=config.HTTP_PORT
    )

    orchestrator = Orchestrator(
        event_bus=event_bus
    )

    event_bus.subscribe(config.LEVEL_OUT_TOPIC, setstatus)
    event_bus.subscribe(config.REQUESTED_OPENING, orchestrator.handle_req_opening)
    event_bus.subscribe(config.MODE_CHANGE, orchestrator.handle_mode_change)
    event_bus.subscribe(config.LEVEL_IN_TOPIC, orchestrator.handle_new_measurement)

    event_bus.subscribe(config.MODE, serial_service.store_new_mode)
    event_bus.subscribe(config.OPENING, serial_service.store_new_opening)
    

    # Create controller (transport-agnostic)
    services = [mqtt_service, serial_service, http_service]
    
    controller = SystemController(
        model=model,
        services=services
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

def getStatus():
    return status

def setstatus(s):
    global status
    status = s