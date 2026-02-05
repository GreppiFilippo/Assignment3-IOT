from abc import ABC, abstractmethod
from typing import TYPE_CHECKING
import time
from models.schemas import SystemState as SystemStateEnum
from core.automatic_substates import (
    AutomaticSubStateBase, 
    NormalSubState
)
from utils.logger import get_logger
import config

if TYPE_CHECKING:
    from core.tank_controller import TankController

logger = get_logger(__name__)


class SystemStateBase(ABC):
    """
    Base class for System States (State Pattern).
    Each state handles its own events and transitions.
    """
    
    @abstractmethod
    def get_state_name(self) -> SystemStateEnum:
        """Return the enum representing this state."""
        pass
    
    @abstractmethod
    def handle_level_event(self, level: float, timestamp: float, controller: 'TankController'):
        """Handle sensor.level event."""
        pass
    
    @abstractmethod
    def handle_button_pressed(self, controller: 'TankController'):
        """Handle button.pressed event."""
        pass
    
    @abstractmethod
    def handle_manual_valve(self, opening: float, controller: 'TankController'):
        """Handle manual.valve_command event."""
        pass
    
    @abstractmethod
    def check_timeout(self, elapsed_ms: int, controller: 'TankController'):
        """Check for timeouts (called periodically)."""
        pass
    
    def on_enter(self, controller: 'TankController'):
        """Called when entering this state."""
        pass
    
    def on_exit(self, controller: 'TankController'):
        """Called when exiting this state."""
        pass


class UnconnectedState(SystemStateBase):
    """
    UNCONNECTED: No sensor data received yet.
    Transitions to AUTOMATIC on first level reading.
    """
    
    def get_state_name(self) -> SystemStateEnum:
        return SystemStateEnum.UNCONNECTED
    
    def handle_level_event(self, level: float, timestamp: float, controller: 'TankController'):
        logger.info(f"First level received ({level}cm) → AUTOMATIC")
        controller.transition_to(AutomaticSystemState())
    
    def handle_button_pressed(self, controller: 'TankController'):
        logger.debug("Button ignored in UNCONNECTED state")
    
    def handle_manual_valve(self, opening: float, controller: 'TankController'):
        logger.debug("Manual valve ignored in UNCONNECTED state")
    
    def check_timeout(self, elapsed_ms: int, controller: 'TankController'):
        pass  # No timeout in UNCONNECTED
    
    def on_enter(self, controller: 'TankController'):
        logger.info("Entered UNCONNECTED state")
        controller.bus.publish(config.MODE_TOPIC, mode=SystemStateEnum.UNCONNECTED)


class ManualState(SystemStateBase):
    """
    MANUAL: Operator controls valve manually.
    Button press transitions to AUTOMATIC.
    """
    
    def get_state_name(self) -> SystemStateEnum:
        return SystemStateEnum.MANUAL
    
    def handle_level_event(self, level: float, timestamp: float, controller: 'TankController'):
        # Still monitor level, but don't act on it
        pass
    
    def handle_button_pressed(self, controller: 'TankController'):
        logger.info("Button pressed: MANUAL → AUTOMATIC")
        controller.transition_to(AutomaticSystemState())
    
    def handle_manual_valve(self, opening: float, controller: 'TankController'):
        logger.debug(f"Manual valve command: {opening}%") #TODO fix control logic
        controller.bus.publish(config.OPENING_TOPIC, opening=opening)
    
    def check_timeout(self, elapsed_ms: int, controller: 'TankController'):
        # Check T2 timeout
        if elapsed_ms > config.T2_TIMEOUT * 1000:
            logger.warning(f"T2 timeout in MANUAL → UNCONNECTED")
            controller.transition_to(UnconnectedState())
    
    def on_enter(self, controller: 'TankController'):
        logger.info("Entered MANUAL mode")
        controller.bus.publish(config.MODE_TOPIC, mode=SystemStateEnum.MANUAL)


class AutomaticSystemState(SystemStateBase):
    """
    AUTOMATIC: FSM controls valve based on water level.
    Manages hierarchical substates (NORMAL, TRACKING, PRE_ALARM, ALARM).
    """
    
    def __init__(self):
        self._current_substate: AutomaticSubStateBase = NormalSubState()
        self._substate_timestamp = int(time.monotonic() * 1000)
    
    def get_state_name(self) -> SystemStateEnum:
        return SystemStateEnum.AUTOMATIC
    
    def handle_level_event(self, level: float, timestamp: float, controller: 'TankController'):
        # Evaluate substate transition
        elapsed_ms = int(time.monotonic() * 1000) - self._substate_timestamp
        new_substate = self._current_substate.evaluate_transition(level, elapsed_ms)
        
        if new_substate is not None:
            self._transition_substate(new_substate, controller)
    
    def handle_button_pressed(self, controller: 'TankController'):
        logger.info("Button pressed: AUTOMATIC → MANUAL")
        controller.transition_to(ManualState())
    
    def handle_manual_valve(self, opening: float, controller: 'TankController'):
        logger.debug("Manual valve ignored in AUTOMATIC mode")
    
    def check_timeout(self, elapsed_ms: int, controller: 'TankController'):
        # Check T2 timeout
        if elapsed_ms > config.T2_TIMEOUT * 1000:
            logger.warning(f"T2 timeout in AUTOMATIC → UNCONNECTED")
            controller.transition_to(UnconnectedState())
    
    def on_enter(self, controller: 'TankController'):
        logger.info("Entered AUTOMATIC mode")
        self._current_substate = NormalSubState()
        self._substate_timestamp = int(time.monotonic() * 1000)
        self._current_substate.on_enter(controller)
        controller.bus.publish(config.MODE_TOPIC, mode=SystemStateEnum.AUTOMATIC)
    
    def _transition_substate(self, new_substate: AutomaticSubStateBase, controller: 'TankController'):
        """Internal: transition between automatic substates."""
        self._current_substate = new_substate
        self._substate_timestamp = int(time.monotonic() * 1000)
        new_substate.on_enter(controller)
    
    @property
    def current_substate(self) -> AutomaticSubStateBase:
        return self._current_substate
