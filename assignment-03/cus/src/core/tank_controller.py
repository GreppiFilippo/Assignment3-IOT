import asyncio
from collections import deque
from collections import deque
import time
from typing import Deque, List
from services.base_service import BaseService
from services.event_bus import EventBus
from models.schemas import LevelReading
from utils.logger import get_logger
import config

# Import system states after config to avoid circular dependency
from core.system_states import *

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
        # Track last value from each source (who) for pot
        self._last_pot_msg: dict[str, float] = {}  # {source_id: last_value}
        # Water level history
        self._water_levels: Deque[LevelReading] = deque(maxlen=20)
        
        # NOTE: Topic subscriptions are done in main.py, not here
        
        logger.info(f"[{self.name}] FSM initialized: {self._current_state.get_state_name()}")

    async def run(self):
        """
        Event-driven FSM: reacts to events via pubsub callbacks.
        Periodic loop only checks for connectivity timeout.
        """
        #print(f"[{self.name}] 🚀 RUN LOOP STARTED")
        while self._running:
            # Check timeout (convert to milliseconds for config comparison)
            current_time = time.time()
            #print(f"[{self.name}] ⏱️ Running periodic check at {current_time}, last level timestamp: {self._last_level_timestamp}")
            elapsed_ms = int((current_time - self._last_level_timestamp) * 1000)
            #print(f"[{self.name}] ⏱️ Elapsed: {elapsed_ms}ms, checking timeout...")
            self._current_state.check_timeout(elapsed_ms, self)
            
            await asyncio.sleep(1.0)

    def _on_level_event(self, reading: dict):
        """Delegate sensor.level event to current state."""
        print(f"[{self.name}] 📊 Level event received: {reading}")

        # Update timestamp
        logger.info(f"[{self.name}] Level event received: {reading}")
        self._last_level_timestamp = time.time()
        # Store in history
        measure = LevelReading(water_level=reading["level"], timestamp=reading["timestamp"])
        self._water_levels.append(measure)
        self.bus.publish(config.LEVELS_OUT_TOPIC, levels=self._water_levels)
        #print(f"[{self.name}] ✅ Level stored: {measure.water_level}cm at {measure.timestamp}")
        
        # Delegate to state
        self._current_state.handle_level_event(measure.water_level, measure.timestamp, self)

    def _on_button_pressed(self, btn):
        """Delegate button.pressed event to current state."""
        if btn:
            print(f"[{self.name}] 🔘 Button pressed!")
            self._current_state.handle_button_pressed(self)

    def _on_manual_valve(self, pot):
        """
        Delegate manual.valve_command event to current state.
        
        Handles both formats:
        - New format: pot={"val": X, "who": "source_id"}
        - Legacy format: value=X (for backward compatibility)
        
        Only propagates value changes from specific sources.
        """
        # Handle legacy format
        if isinstance(pot, dict) and "val" in pot and "who" in pot:
            value = pot["val"]
            source_id = pot["who"]
            if source_id in self._last_pot_msg and abs(value - self._last_pot_msg[source_id]) < config.TOLERANCE:
                return
            self._last_pot_msg[source_id] = value
            self._current_state.handle_manual_valve(value, self)

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
