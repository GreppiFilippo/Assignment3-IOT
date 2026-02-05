import asyncio
import signal
from services.event_bus import EventBus
from services.serial_service import SerialService
from services.mqtt_service import MQTTService
from core.tank_controller import TankController
from config import *

async def main():
    # 1. Initialize the Single Instance of the Event Bus
    bus = EventBus()

    # 2. Instantiate the Core Controller (Domain Layer)
    # The controller logic is now decoupled from hardware
    controller = TankController(event_bus=bus)

    # 3. Instantiate Infrastructure Adapters
    serial_service = SerialService(
        port="/dev/ttyUSB0", 
        baudrate=9600, 
        event_bus=bus,
        send_interval=0.5
    )
    
    # Let's assume you have an MqttService similar to SerialService
    mqtt_service = MQTTService(
        broker=MQTT_BROKER_HOST,
        port=MQTT_BROKER_PORT,
        event_bus=bus,
        qos=1
    )

    # 4. Wiring: Configure Pub/Sub Topics for each service
    # This is the "Registry" where you define the communication flow
    
    # Serial: Reads POT_VAL from Arduino -> Publishes to "sensor.level"
    #         Listens to "cmd.valve" to send to Arduino
    serial_service.configure_messaging(
        pub_topic="sensor.level",
        sub_topics=["cmd.valve"]
    )

    # MQTT: Publishes internal "sensor.level" to the cloud
    #       Listens to cloud "remote/control" -> Publishes to "cmd.valve"
    mqtt_service.configure_messaging(
        pub_topic="cmd.valve",
        sub_topics=["sensor.level"]
    )

    # 5. Start all services concurrently
    # asyncio.gather runs them as concurrent tasks in the same event loop
    services = [serial_service, mqtt_service]
    
    logger.info("Starting all system services...")
    await asyncio.gather(*(service.start() for service in services))

    # 6. Keep the main alive and handle graceful shutdown
    stop_event = asyncio.Event()
    
    # Handle CTRL+C
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    try:
        await stop_event.wait()
    finally:
        logger.info("Shutting down services...")
        await asyncio.gather(*(service.stop() for service in services), return_exceptions=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass