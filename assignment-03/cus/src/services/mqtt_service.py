import asyncio
import json
import paho.mqtt.client as mqtt
from typing import List, Dict, Optional
from services.event_bus import EventBus
from .base_service import BaseService
from utils.logger import get_logger

logger = get_logger(__name__)

class MQTTService(BaseService):
    """
    MQTT Infrastructure Adapter.
    Acts as a bridge between an external MQTT Broker and the internal EventBus.
    """

    def __init__(self, broker: str, port: int, event_bus: EventBus, qos: int = 0):
        """
        Initialize the MQTT service.
        
        :param broker: MQTT broker address.
        :param port: MQTT broker port.
        :param event_bus: Injected instance of EventBus.
        :param qos: Quality of Service level.
        """
        super().__init__("mqtt_service", event_bus)
        self.broker = broker
        self.port = port
        self.qos = qos
        
        # Paho Client setup
        self._client = mqtt.Client()
        self._connected = False
        
        # Topic Mapping: { "mqtt/topic": "bus.topic" }
        self._incoming_map: Dict[str, str] = {}
        # Internal topics to listen to for publishing to MQTT: { "bus.topic": "mqtt/topic" }
        self._outgoing_map: Dict[str, str] = {}

        # Configure Callbacks
        self._client.on_connect = self._on_mqtt_connect
        self._client.on_message = self._on_mqtt_message
        self._client.on_disconnect = self._on_mqtt_disconnect

    def configure_messaging(self, incoming: Dict[str, str], outgoing: Dict[str, str]):
        """
        Wire MQTT topics to internal Event Bus topics.
        
        :param incoming: Map of { "mqtt/topic": "internal.bus.topic" }
        :param outgoing: Map of { "internal.bus.topic": "external/mqtt/topic" }
        """
        self._incoming_map = incoming
        self._outgoing_map = outgoing
        
        # Subscribe to internal bus topics to forward them to MQTT
        for bus_topic in self._outgoing_map.keys():
            self.bus.subscribe(bus_topic, self._on_internal_bus_update)
            logger.info(f"[{self.name}] Listening to Bus topic: {bus_topic}")

    async def setup(self):
        """Establish connection with the MQTT broker."""
        try:
            # Connect using the thread executor to prevent blocking the event loop
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self._client.connect(self.broker, self.port, keepalive=60))
            
            # Start the background threaded loop provided by paho-mqtt
            self._client.loop_start()
            logger.info(f"[{self.name}] Connecting to broker {self.broker}:{self.port}...")
        except Exception as e:
            logger.error(f"[{self.name}] Failed to connect to MQTT broker: {e}")

    async def run(self):
        """Monitor connection status and maintain the service alive."""
        while self._running:
            if not self._connected:
                # Connection logic is handled by paho's loop_start auto-reconnect,
                # but we can add custom health checks here.
                await asyncio.sleep(5)
            await asyncio.sleep(1)

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback invoked when connected to the broker."""
        if rc == 0:
            self._connected = True
            logger.info(f"[{self.name}] Successfully connected to MQTT broker.")
            # Subscribe to all mapped external topics
            for mqtt_topic in self._incoming_map.keys():
                client.subscribe(mqtt_topic, qos=self.qos)
                logger.info(f"[{self.name}] Subscribed to MQTT: {mqtt_topic}")
        else:
            logger.error(f"[{self.name}] Connection failed with result code {rc}")

    def _on_mqtt_disconnect(self, client, userdata, rc):
        """Callback invoked when disconnected."""
        self._connected = False
        logger.warning(f"[{self.name}] Disconnected from broker (rc: {rc}).")

    def _on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages and publish them to the internal Event Bus."""
        try:
            mqtt_topic = msg.topic
            bus_topic = self._incoming_map.get(mqtt_topic)
            
            if bus_topic:
                payload = json.loads(msg.payload.decode("utf-8"))
                logger.debug(f"[{self.name}] MQTT -> Bus: {mqtt_topic} to {bus_topic}")
                # Use the injected bus to notify the rest of the system
                self.bus.publish(bus_topic, **payload)
        except Exception as e:
            logger.error(f"[{self.name}] Error processing MQTT message: {e}")

    def _on_internal_bus_update(self, **kwargs):
        """Callback for internal bus events that need to be sent to the MQTT broker."""
        # Find the original bus topic from the event (Topic detection depends on EventBus implementation)
        # Assuming your Bus implementation can pass the topic or you use a specific callback
        # For simplicity, this handles data destined for the broker:
        try:
            # We iterate to find which MQTT topic maps to this internal data
            # In a more advanced version, use separate methods for each topic
            for bus_topic, mqtt_topic in self._outgoing_map.items():
                payload = json.dumps(kwargs)
                self._client.publish(mqtt_topic, payload, qos=self.qos)
                logger.debug(f"[{self.name}] Bus -> MQTT: {mqtt_topic}")
        except Exception as e:
            logger.error(f"[{self.name}] Error publishing to MQTT: {e}")

    async def cleanup(self):
        """Cleanly disconnect from the broker."""
        logger.info(f"[{self.name}] Cleaning up MQTT resources...")
        self._client.loop_stop()
        self._client.disconnect()