from pubsub import pub
from typing import Callable
from utils.logger import get_logger

logger = get_logger(__name__)

class EventBus:
    """
    Instance-based Event Bus wrapper.
    Hides pypubsub and allows true Dependency Injection.
    """

    def __init__(self):
        # We use the global pub instance internally, 
        # but the services only interact with this wrapper instance.
        self._engine = pub

    def publish(self, topic: str, **kwargs):
        """Publish an event to a specific topic."""
        try:
            self._engine.sendMessage(topic, **kwargs)
            logger.debug(f"[Bus] Published to {topic} with {kwargs}")
        except Exception as e:
            logger.error(f"[Bus] Error publishing to {topic}: {e}")

    def subscribe(self, topic: str, callback: Callable):
        """Subscribe a listener to a specific topic."""
        try:
            self._engine.subscribe(callback, topic)
            logger.info(f"[Bus] New subscription on: {topic}")
        except Exception as e:
            logger.error(f"[Bus] Error subscribing to {topic}: {e}")