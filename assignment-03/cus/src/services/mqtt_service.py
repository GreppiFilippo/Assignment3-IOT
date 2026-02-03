import asyncio
import json
from .base_service import BaseService
import paho.mqtt.client as mqtt
from typing import Callable
from utils.logger import get_logger
from .event_dispatcher import EventDispatcher

logger = get_logger(__name__)

class MQTTService(BaseService):
    """
    MQTT service for receiving messages from MQTT broker.
    """

    def __init__(
        self, 
        event_dispatcher: EventDispatcher, 
        broker: str, 
        port: int, 
        topics: str | list[str],
        qos: int = 0
    ):
        """
        Initialize MQTT service.
        
        :param event_dispatcher: Event dispatcher for inter-service communication
        :type event_dispatcher: EventDispatcher
        :param broker: MQTT broker address
        :type broker: str
        :param port: MQTT broker port
        :type port: int
        :param topics: MQTT topics to subscribe to
        :type topics: str | list[str]
        :param qos: Quality of Service level (0: at most once, 1: at least once, 2: exactly once)
        :type qos: int
        """
        super().__init__("mqtt_service", event_dispatcher)
        self.broker = broker
        self.port = port
        self.topics = [topics] if isinstance(topics, str) else topics
        self.qos = max(0, min(2, qos))  # Clamp between 0 and 2
        self._client = mqtt.Client()
        self._loop = None
        self._handlers: dict[str, list[Callable[..., None]]] = {}
        self._raw_handlers: list[Callable[[str], None]] = []

        self._client.on_connect = self.__on_connect
        self._client.on_message = self.__on_message
        self._client.on_disconnect = self.__on_disconnect

    def register_handler(self, key: str, callback: Callable[..., None]) -> 'MQTTService':
        """
        Register a handler for a specific key in MQTT messages (Builder pattern).
        Multiple handlers can be registered for the same key.
        
        Args:
            key: Key to match in MQTT message payload
            callback: Handler function to call when key is found
        
        Returns:
            Self for method chaining
        
        Example:
            mqtt.register_handler('level', handle_level) \
                .register_handler('status', handle_status)
        """
        if key not in self._handlers:
            self._handlers[key] = []
        self._handlers[key].append(callback)
        logger.info(f"{self.name} registered handler for '{key}'")
        return self
    
    def register_payload_handler(self, callback: Callable[[str], None]) -> 'MQTTService':
        """
        Register a handler that receives the raw payload string.
        Handler is responsible for parsing (JSON, plain text, etc).
        
        Args:
            callback: Handler function that receives the raw payload string
        
        Returns:
            Self for method chaining
        
        Example:
            mqtt.register_payload_handler(handle_raw_payload)
        """
        self._raw_handlers.append(callback)
        logger.info(f"{self.name} registered raw payload handler")
        return self

    async def run(self):
        """Run MQTT service"""
        self._loop = asyncio.get_running_loop()
        
        logger.info(f"{self.name} connecting to broker {self.broker}:{self.port}")
        
        try:
            self._client.connect(self.broker, self.port, keepalive=60)
        except Exception as e:
            logger.error(f"{self.name} failed to connect to broker: {e}")
            return
            
        self._client.loop_start()

        try:
            while self._running:
                await asyncio.sleep(0.1)
        finally:
            logger.info(f"{self.name} stopping MQTT loop")
            self._client.loop_stop()
            self._client.disconnect()

    def __on_connect(self, client, userdata, flags, rc):
        """Callback invoked when connection to MQTT broker is established."""
        if rc == 0:
            logger.info(f"{self.name} connected to broker")
            for topic in self.topics:
                client.subscribe(topic, qos=self.qos)
                logger.info(f"{self.name} subscribed to topic: {topic} (QoS {self.qos})")
        else:
            logger.error(f"{self.name} failed to connect, rc={rc}")

    def __on_disconnect(self, client, userdata, rc):
        """Callback invoked when disconnected from MQTT broker."""
        logger.warning(f"{self.name} disconnected with rc={rc}")

    def __on_message(self, client, userdata, msg):
        """Callback invoked when message is received from MQTT broker."""
        if self._loop is None:
            logger.warning(f"{self.name} received message before event loop initialized")
            return
            
        try:
            payload = msg.payload.decode("utf-8")
            
            # Dispatch raw payload to raw handlers (no parsing)
            for callback in self._raw_handlers:
                self._loop.call_soon_threadsafe(callback, payload)
            
            # Try parsing as JSON for key-based handlers
            try:
                data = json.loads(payload)
                logger.debug(f"{self.name} received JSON message: {data}")
                
                # Dispatch to registered key handlers (receive single values)
                for key, callbacks in self._handlers.items():
                    if key in data:
                        for callback in callbacks:
                            self._loop.call_soon_threadsafe(callback, data[key])
            
            except json.JSONDecodeError:
                # Not JSON, skip key-based handlers
                logger.debug(f"{self.name} received non-JSON message: {payload}")

        except Exception as e:
            logger.exception(f"{self.name} failed to process MQTT message: {e}")
