import asyncio
from .base_service import BaseService
import paho.mqtt.client as mqtt
from utils.logger import get_logger
from .event_bus import EventBus
import json

logger = get_logger(__name__)

class MQTTService(BaseService):
    """
    MQTT service for receiving messages from MQTT broker.
    Publishes received messages to EventBus for decoupled communication.
    """

    def __init__(
        self, 
        broker: str, 
        port: int, 
        topics: str | list[str],
        qos: int = 0
    ):
        """
        Initialize MQTT service.
        
        :param broker: MQTT broker address
        :type broker: str
        :param port: MQTT broker port
        :type port: int
        :param topics: MQTT topics to subscribe to
        :type topics: str | list[str]
        :param qos: Quality of Service level (0: at most once, 1: at least once, 2: exactly once)
        :type qos: int
        """
        super().__init__("mqtt_service", None)  # No event_dispatcher needed
        self.broker = broker
        self.port = port
        self.topics = [topics] if isinstance(topics, str) else topics
        self.qos = max(0, min(2, qos))  # Clamp between 0 and 2
        self._client = mqtt.Client()
        self._loop = None
        self._connected = False  # Track connection status

        self._client.on_connect = self.__on_connect
        self._client.on_message = self.__on_message
        self._client.on_disconnect = self.__on_disconnect

    async def run(self):
        """Run MQTT service with auto-reconnect"""
        self._loop = asyncio.get_running_loop()
        
        logger.info(f"{self.name} connecting to broker {self.broker}:{self.port}")
        
        loop_started = False
        retry_interval = 5  # seconds between reconnection attempts
        
        try:
            self._client.connect(self.broker, self.port, keepalive=60)
            self._client.loop_start()
            loop_started = True
        except Exception as e:
            logger.error(f"{self.name} failed to connect to broker: {e}")
            logger.info(f"{self.name} will retry connection every {retry_interval}s")

        try:
            while self._running:
                # Try to reconnect if not connected
                if not self._connected and not loop_started:
                    try:
                        logger.info(f"{self.name} attempting to reconnect...")
                        self._client.connect(self.broker, self.port, keepalive=60)
                        self._client.loop_start()
                        loop_started = True
                    except Exception as e:
                        logger.debug(f"{self.name} reconnect failed: {e}")
                        # Sleep in small intervals to allow quick shutdown
                        for _ in range(retry_interval * 10):
                            if not self._running:
                                break
                            await asyncio.sleep(0.1)
                        continue
                
                await asyncio.sleep(0.1)
        finally:
            if loop_started:
                logger.info(f"{self.name} stopping MQTT loop")
                self._client.loop_stop()
                self._client.disconnect()

    def __on_connect(self, client, userdata, flags, rc):
        """Callback invoked when connection to MQTT broker is established."""
        if rc == 0:
            self._connected = True
            logger.info(f"{self.name} connected to broker")
            for topic in self.topics:
                client.subscribe(topic, qos=self.qos)
                logger.info(f"{self.name} subscribed to topic: {topic} (QoS {self.qos})")
        else:
            self._connected = False
            logger.error(f"{self.name} failed to connect, rc={rc}")

    def __on_disconnect(self, client, userdata, rc):
        """Callback invoked when disconnected from MQTT broker."""
        self._connected = False
        if rc == 0:
            logger.info(f"{self.name} disconnected cleanly")
        else:
            logger.warning(f"{self.name} disconnected unexpectedly (rc={rc}), will attempt reconnect")

    def __on_message(self, client, userdata, msg):
        """Callback invoked when message is received from MQTT broker."""
        if self._loop is None:
            logger.warning(f"{self.name} received message before event loop initialized")
            return
            
        try:
            payload = msg.payload.decode("utf-8")
            logger.debug(f"{self.name} received MQTT message: {payload}")
            data = json.loads(payload)

            for topic, event_data in data.items():
                if not isinstance(event_data, dict):
                    logger.warning(f"Skipping topic {topic}: payload not dict")
                    continue

                asyncio.run_coroutine_threadsafe(
                    logger.debug("Pubblico su" + topic + " i dati " + str(event_data)),
                    EventBus.publish(topic, **event_data),
                    self._loop
                )

        except Exception as e:
            logger.exception(f"{self.name} failed to process MQTT message: {e}")
