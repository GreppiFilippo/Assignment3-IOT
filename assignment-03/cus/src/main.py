import asyncio
import signal
from services.event_bus import EventBus
from services.serial_service import SerialService
from services.mqtt_service import MQTTService
from services.http_service import HttpService
from core.tank_controller import TankController
from core.system_states import AutomaticSystemState
from config import *
from utils.logger import get_logger


logger = get_logger(__name__)

async def main():
    # 1. Initialize the Single Instance of the Event Bus
    bus = EventBus()

    # 2. Instantiate the Event-Driven FSM Controller
    controller = TankController(event_bus=bus)

    bus.subscribe(MODE_CHANGE_TOPIC, controller._on_button_pressed)
    bus.subscribe(POT_TOPIC, controller._on_manual_valve)
    bus.subscribe(LEVEL_IN_TOPIC, controller._on_level_event)
    
    # 3. Instantiate Infrastructure Adapters
    serial_service = SerialService(
        port=SERIAL_PORT, 
        baudrate=SERIAL_BAUDRATE, 
        event_bus=bus,
        send_interval=SERIAL_SEND_INTERVAL
    )

    bus.subscribe(MODE_TOPIC, serial_service.on_mode_change)
    bus.subscribe(OPENING_TOPIC, serial_service.on_valve_command)
    
    mqtt_service = MQTTService(
        broker=MQTT_BROKER_HOST,
        port=MQTT_BROKER_PORT,
        event_bus=bus,
        qos=1
    )
    
    http_service = HttpService(
        event_bus=bus,
        host=HTTP_HOST,
        port=HTTP_PORT,
        publish_interval=10.0,
        api_prefix="/api/v1"
    )

    
    # Map topics to REST endpoints
    http_service.map_topic_to_endpoint(OPENING_TOPIC, "POST")
    http_service.map_topic_to_endpoint(MODE_CHANGE_TOPIC, "POST")
    
    # Add status endpoint
    @http_service._app.get("/api/v1/status")
    async def get_status():
        """Get current system status."""
        state = controller.state
        
        # Get substate if in AUTOMATIC
        substate = None
        if isinstance(controller._current_state, AutomaticSystemState):
            substate = controller._current_state.current_substate.get_state_name().value
        
        return {
            "system_state": state.value,
            "automatic_substate": substate,
            "current_level": controller.current_level,
            "water_levels_count": len(controller.water_levels)
        }

    # 5. Start all services concurrently
    services = [controller, serial_service, mqtt_service, http_service]
    
    logger.info("🚀 Starting all system services...")
    await asyncio.gather(*(service.start() for service in services))

    # 6. Graceful shutdown handler
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    try:
        await stop_event.wait()
    finally:
        logger.info("🛑 Shutting down services...")
        await asyncio.gather(*(service.stop() for service in services), return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass