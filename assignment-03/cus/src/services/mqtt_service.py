import asyncio
import json
import time
import paho.mqtt.client as mqtt
from typing import Dict, Optional
from services.event_bus import EventBus
from .base_service import BaseService
from utils.logger import get_logger

logger = get_logger(__name__)

class MQTTService(BaseService):
    """
    MQTT Infrastructure Adapter.
    Acts as a bridge between an external MQTT Broker and the internal EventBus.
    """

    def __init__(self, broker: str, port: int, event_bus: EventBus, qos: int = 0, publish_interval: float = 5.0):
        """
        Initialize the MQTT service.
        
        :param broker: MQTT broker address.
        :param port: MQTT broker port.
        :param event_bus: Injected instance of EventBus.
        :param qos: Quality of Service level.
        :param publish_interval: Interval in seconds for periodic publishing.
        """
        super().__init__("mqtt_service", event_bus)
        self.broker = broker
        self.port = port
        self.qos = qos
        self._publish_interval = publish_interval
        self._last_publish_time = 0.0
        
        # Paho Client setup
        self._client = mqtt.Client()
        self._connected = False
        
        # Topic Mapping: { "mqtt/topic": "bus.topic" }
        self._incoming_map: Dict[str, str] = {}
        # Internal topics to listen to for publishing to MQTT: { "bus.topic": "mqtt/topic" }
        self._outgoing_map: Dict[str, str] = {}
        # Cache ultimo stato ricevuto per pubblicazione periodica
        self._last_bus_data: Dict[str, dict] = {}

        # Configure Callbacks
        self._client.on_connect = self._on_mqtt_connect
        self._client.on_message = self._on_mqtt_message
        self._client.on_disconnect = self._on_mqtt_disconnect

    def configure_messaging(self, incoming: Optional[Dict[str, str]] = None, outgoing: Optional[Dict[str, str]] = None):
        """
        Wire MQTT topics to internal Event Bus topics.
        
        :param incoming: Map of { "mqtt/topic": "internal.bus.topic" }
                        MQTT riceve da broker → pubblica su bus
        :param outgoing: Map of { "internal.bus.topic": "external/mqtt/topic" }
                        Bus riceve eventi → pubblica su MQTT broker
        """
        if incoming:
            self._incoming_map = incoming
            logger.info(f"[{self.name}] Incoming mapping: {incoming}")
        
        if outgoing:
            self._outgoing_map = outgoing
            # Subscribe to internal bus topics to forward them to MQTT
            for bus_topic in self._outgoing_map.keys():
                # Crea callback dedicata per ogni topic
                callback = self._make_outgoing_handler(bus_topic)
                self.bus.subscribe(bus_topic, callback)
                logger.info(f"[{self.name}] Subscribed to bus: {bus_topic} → MQTT: {outgoing[bus_topic]}")

    async def setup(self):
        """Establish connection with the MQTT broker."""
        print(f"[{self.name}] setup() called - incoming map: {self._incoming_map}")
        logger.info(f"[{self.name}] setup() called - incoming map: {self._incoming_map}")
        try:
            print(f"[{self.name}] Attempting to connect to broker {self.broker}:{self.port}...")
            logger.info(f"[{self.name}] Attempting to connect to broker {self.broker}:{self.port}...")
            # Connect using the thread executor to prevent blocking the event loop
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, lambda: self._client.connect(self.broker, self.port, keepalive=60))
            
            # Start the background threaded loop provided by paho-mqtt
            self._client.loop_start()
            print(f"[{self.name}] MQTT loop started, waiting for connection callback...")
            logger.info(f"[{self.name}] MQTT loop started, waiting for connection callback...")
        except Exception as e:
            print(f"[{self.name}] Failed to connect to MQTT broker: {e}")
            logger.error(f"[{self.name}] Failed to connect to MQTT broker: {e}")

    async def run(self):
        """Monitor connection status and maintain the service alive."""
        logger.info(f"[{self.name}] run() started, entering main loop...")
        while self._running:
            if self._connected:
                # Pubblicazione periodica
                now = time.monotonic()
                if now - self._last_publish_time >= self._publish_interval:
                    await self._periodic_publish()
                    self._last_publish_time = now
            else:
                # Connection logic is handled by paho's loop_start auto-reconnect
                await asyncio.sleep(5)
            await asyncio.sleep(1)
        logger.info(f"[{self.name}] run() exiting...")
    
    async def _periodic_publish(self):
        """Pubblica periodicamente i dati in cache su MQTT."""
        try:
            for bus_topic, data in self._last_bus_data.items():
                mqtt_topic = self._outgoing_map.get(bus_topic)
                if mqtt_topic and data:
                    payload = json.dumps(data)
                    self._client.publish(mqtt_topic, payload, qos=self.qos)
                    logger.debug(f"[{self.name}] Periodic publish to {mqtt_topic}")
        except Exception as e:
            logger.error(f"[{self.name}] Error in periodic publish: {e}")

    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback invoked when connected to the broker."""
        if rc == 0:
            self._connected = True
            print(f"[{self.name}] ✅ Successfully connected to MQTT broker.")
            logger.info(f"[{self.name}] Successfully connected to MQTT broker.")
            # Subscribe to all mapped external topics
            for mqtt_topic in self._incoming_map.keys():
                client.subscribe(mqtt_topic, qos=self.qos)
                print(f"[{self.name}] 📡 Subscribed to MQTT: {mqtt_topic}")
                logger.info(f"[{self.name}] Subscribed to MQTT: {mqtt_topic}")
        else:
            print(f"[{self.name}] ❌ Connection failed with result code {rc}")
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
                print(f"[{self.name}] 📨 MQTT message: topic={mqtt_topic}, type={type(payload).__name__}, payload={payload}")
                logger.info(f"[{self.name}] MQTT -> Bus: {mqtt_topic} to {bus_topic}, payload type: {type(payload)}, payload: {payload}")
                
                # Handle different payload types
                if isinstance(payload, dict):
                    # Fix timestamp if present (ESP sends uptime, we need absolute time)
                    if 'reading' in payload and isinstance(payload['reading'], dict):
                        if 'timestamp' in payload['reading']:
                            # Replace ESP uptime with current server time
                            payload['reading']['timestamp'] = time.time()
                            print(f"[{self.name}] 🕐 Timestamp fixed to current time: {payload['reading']['timestamp']}")
                    
                    # Use the injected bus to notify the rest of the system
                    self.bus.publish(bus_topic, **payload)
                    print(f"[{self.name}] ✅ Published to bus: {bus_topic}")
                else:
                    # Skip non-dict payloads (e.g., simple integers or strings)
                    print(f"[{self.name}] ⚠️  Skipping non-dict payload: {payload}")
                    logger.warning(f"[{self.name}] Skipping non-dict payload from {mqtt_topic}: {payload}")
                    
        except Exception as e:
            print(f"[{self.name}] ❌ Error processing MQTT message: {e}")
            logger.error(f"[{self.name}] Error processing MQTT message: {e}")

    def _make_outgoing_handler(self, bus_topic: str):
        """Factory per creare callback specifiche per ogni topic in uscita."""
        mqtt_topic = self._outgoing_map[bus_topic]
        
        def handler(**kwargs):
            try:
                # Salva in cache per pubblicazione periodica
                self._last_bus_data[bus_topic] = kwargs
                
                # Pubblica immediatamente su MQTT
                payload = json.dumps(kwargs)
                self._client.publish(mqtt_topic, payload, qos=self.qos)
                logger.debug(f"[{self.name}] Bus({bus_topic}) → MQTT({mqtt_topic})")
            except Exception as e:
                logger.error(f"[{self.name}] Error publishing to MQTT: {e}")
        
        return handler

    async def cleanup(self):
        """Cleanly disconnect from the broker."""
        logger.info(f"[{self.name}] Cleaning up MQTT resources...")
        self._client.loop_stop()
        self._client.disconnect()