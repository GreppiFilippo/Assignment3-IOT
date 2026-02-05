import asyncio
import time
from typing import List
from services.base_service import BaseService
from services.event_bus import EventBus
from models.schemas import LevelReading
from utils.logger import get_logger
import config

# Import system states after config to avoid circular dependency
from core.system_states import SystemStateBase, UnconnectedState

logger = get_logger(__name__)


class TankController(BaseService):
    """
    Minimal FSM Controller (State Pattern).
    
    Responsibilities:
    - Maintain current system state
    - Store water level history
    - Delegate events to current state
    - Track timestamps for timeout checks
    
    All business logic is in state classes.
    """

    def __init__(self, event_bus: EventBus):
        super().__init__("tank_controller", event_bus)
        
        # State management
        self._current_state: SystemStateBase = UnconnectedState()
        self._last_level_timestamp = time.time()  # Unix timestamp in seconds
        self._who = dict()
        # Water level history
        self._water_levels: List[LevelReading] = []
        
        # Subscribe to domain events
        self.bus.subscribe("sensor.level", self._on_level_event)
        self.bus.subscribe("button.pressed", self._on_button_pressed)
        self.bus.subscribe("manual.valve_command", self._on_manual_valve)
        
        logger.info(f"[{self.name}] FSM initialized: {self._current_state.get_state_name()}")

    async def run(self):
        """
        Event-driven FSM: reacts to events via pubsub callbacks.
        Periodic loop only checks for connectivity timeout.
        """
        while self._running:
            # Check timeout (convert to milliseconds for config comparison)
            elapsed_ms = int((time.time() - self._last_level_timestamp) * 1000)
            self._current_state.check_timeout(elapsed_ms, self)
            
            await asyncio.sleep(1.0)

    def _on_level_event(self, reading: dict):
        """Delegate sensor.level event to current state."""
        print(f"[{self.name}] 📊 Level event received: {reading}")
        logger.info(f"[{self.name}] Level event received: {reading}")
        
        # Store in history
        measure = LevelReading(water_level=reading["level"], timestamp=reading["timestamp"])
        self._water_levels.append(measure)
        
        # Update timestamp
        self._last_level_timestamp = measure.timestamp
        
        print(f"[{self.name}] ✅ Level stored: {measure.water_level}cm at {measure.timestamp}")
        
        # Delegate to state
        self._current_state.handle_level_event(measure.water_level, measure.timestamp, self)

    def _on_button_pressed(self, btn):
        """Delegate button.pressed event to current state."""
        self._current_state.handle_button_pressed(self)

    def _on_manual_valve(self, pot: dict):
        """Delegate manual.valve_command event to current state."""
        if self._who.get(who) != value:
            logger.info(f"Manual valve command from {who}: {value}")
            self._who[who] = value
            opening = value
        self._current_state.handle_manual_valve(opening, self)

    def transition_to(self, new_state: SystemStateBase):
        """
        Transition to a new system state.
        Called by states themselves (not by external code).
        """
        old_state = self._current_state
        old_state.on_exit(self)
        
        self._current_state = new_state
        logger.info(f"State transition: {old_state.get_state_name().value} → {new_state.get_state_name().value}")
        
        new_state.on_enter(self)

    # Public accessors for status queries
    @property
    def state(self):
        return self._current_state.get_state_name()
    
    @property
    def water_levels(self) -> List[LevelReading]:
        return self._water_levels
    
    @property
    def current_level(self) -> float:
        return self._water_levels[-1].water_level if self._water_levels else 0.0
