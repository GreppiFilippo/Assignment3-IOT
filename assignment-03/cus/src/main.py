import asyncio
import signal
import time
from services.event_bus import EventBus
from services.serial_service import SerialService
from services.mqtt_service import MQTTService, QOSLevel
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

    # Configure serial messaging (inject dependencies)
    serial_service.configure_messaging(
        incoming={
            "pot": POT_TOPIC,    # Serial "pot" -> bus POT_TOPIC
            "btn": MODE_CHANGE_TOPIC  # Serial "btn" -> bus MODE_CHANGE_TOPIC
        },
        outgoing_state_keys=["mode", "valve"],
        initial_state={"mode": "UNCONNECTED", "valve": 0.0} # Initial serial state, for safety
    )
    
    # Subscribe to bus topics to update serial state
    bus.subscribe(MODE_TOPIC, lambda **kw: serial_service.on_state_change("mode", **kw))
    bus.subscribe(OPENING_TOPIC, lambda **kw: serial_service.on_state_change("valve", **kw))
    
    mqtt_service = MQTTService(
        broker=MQTT_BROKER_HOST,
        port=MQTT_BROKER_PORT,
        event_bus=bus,
        qos=QOSLevel.AT_LEAST_ONCE,
    )
    
    # Configure MQTT to only receive messages from broker
    mqtt_service.configure_messaging(
        incoming={
            "tank/level": LEVEL_IN_TOPIC,  # MQTT tank/level -> bus level_in
        }
    )
    
    http_service = HttpService(
        event_bus=bus,
        host=HTTP_HOST,
        port=HTTP_PORT,
        publish_interval=10.0,
        api_prefix="/api/v1"
    )

    # Register HTTP endpoints (inject dependencies)
    http_service.add_get_endpoint("/mode", "mode", "mode")
    http_service.add_get_endpoint("/levels", "levels", "levels")
    http_service.add_get_endpoint("/valve", "valve", "valve")
    http_service.add_post_endpoint("/pot", POT_TOPIC, "pot")
    
    # Subscribe to bus topics to update HTTP state
    bus.subscribe(LEVELS_OUT_TOPIC, lambda **kw: http_service.on_state_update("levels", **kw))
    bus.subscribe(MODE_TOPIC, lambda **kw: http_service.on_state_update("mode", **kw))
    bus.subscribe(OPENING_TOPIC, lambda **kw: http_service.on_state_update("valve", **kw))
    
    # 5. Start all services concurrently
    services = [controller, serial_service, mqtt_service, http_service]  # TEST: Serial + MQTT
    
    print("=" * 80)
    print("🚀 Starting all system services...")
    print(f"Services to start: {[s.name for s in services]}")
    print("=" * 80)
    logger.info("🚀 Starting all system services...")
    logger.info(f"Services to start: {[s.name for s in services]}")
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