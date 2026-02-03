"""
Async-safe wrapper for PyPubSub.

Provides a simple event bus for decoupled communication between services.
Uses PyPubSub library for robust signal dispatching.
"""

import asyncio
from typing import Callable, Any
from pubsub import pub
from utils.logger import get_logger

logger = get_logger(__name__)


class EventBus:
    """
    Async-safe event bus using PyPubSub.
    
    Simplified interface for publish-subscribe pattern:
    - Subscribe: listen to events
    - Publish: send events (async-safe)
    
    Example:
        # Subscribe
        EventBus.subscribe('tank.level', controller.on_level)
        
        # Publish
        await EventBus.publish('tank.level', level=45.5)
    """
    
    @staticmethod
    def subscribe(topic: str, callback: Callable[..., Any]) -> None:
        """
        Subscribe to an event topic.
        
        Args:
            topic: Event topic (e.g., 'tank.level', 'valve.set')
            callback: Function to call when event is published
                     Can be sync or async function
        
        Example:
            def on_level(level):
                print(f"Level: {level}")
            
            EventBus.subscribe('tank.level', on_level)
        """
        # Wrap async callbacks to run as tasks
        if asyncio.iscoroutinefunction(callback):
            def async_wrapper(**kwargs):
                asyncio.create_task(callback(**kwargs))
            pub.subscribe(async_wrapper, topic)
            logger.debug(f"Subscribed async callback to '{topic}'")
        else:
            pub.subscribe(callback, topic)
            logger.debug(f"Subscribed sync callback to '{topic}'")
    
    @staticmethod
    def unsubscribe(topic: str, callback: Callable[..., Any]) -> None:
        """
        Unsubscribe from an event topic.
        
        Args:
            topic: Event topic
            callback: Previously subscribed callback
        """
        pub.unsubscribe(callback, topic)
        logger.debug(f"Unsubscribed callback from '{topic}'")
    
    @staticmethod
    async def publish(topic: str, **kwargs) -> None:
        """
        Publish an event (async-safe).
        
        Args:
            topic: Event topic
            **kwargs: Event data as keyword arguments
        
        Example:
            await EventBus.publish('tank.level', level=45.5, timestamp=123456)
        """
        loop = asyncio.get_event_loop()
        # Run in executor to avoid blocking if callbacks are slow
        await loop.run_in_executor(None, pub.sendMessage, topic, **kwargs)
        logger.debug(f"Published event '{topic}' with data: {kwargs}")
    
    @staticmethod
    def publish_sync(topic: str, **kwargs) -> None:
        """
        Publish an event (synchronous, for non-async contexts).
        
        Args:
            topic: Event topic
            **kwargs: Event data as keyword arguments
        
        Example:
            EventBus.publish_sync('tank.level', level=45.5)
        """
        pub.sendMessage(topic, **kwargs)
        logger.debug(f"Published sync event '{topic}' with data: {kwargs}")
    
    @staticmethod
    def unsubscribe_all(topic: str) -> None:
        """
        Remove all subscribers from a topic.
        
        Args:
            topic: Event topic to clear
        """
        pub.unsubAll(topic)
        logger.debug(f"Unsubscribed all callbacks from '{topic}'")
    
    @staticmethod
    def get_topics() -> list[str]:
        """
        Get all registered topics.
        
        Returns:
            List of topic names
        """
        return [t.getName() for t in pub.getDefaultTopicMgr().getTopics()]
