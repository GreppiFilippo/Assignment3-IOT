from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
from models.schemas import AutomaticState as AutomaticStateEnum
from utils.logger import get_logger
import config

if TYPE_CHECKING:
    from core.tank_controller import TankController

logger = get_logger(__name__)


class AutomaticSubStateBase(ABC):
    """
    Base class for Automatic Sub-States.
    Each substate manages its own transitions and valve commands.
    """
    
    @abstractmethod
    def get_state_name(self) -> AutomaticStateEnum:
        """Return the enum representing this substate."""
        pass
    
    @abstractmethod
    def get_valve_opening(self) -> float:
        """Return valve opening percentage for this substate."""
        pass
    
    @abstractmethod
    def evaluate_transition(
        self, 
        level: float, 
        elapsed_ms: int
    ) -> Optional['AutomaticSubStateBase']:
        """
        Evaluate if a transition should occur.
        Returns new substate if transition needed, None otherwise.
        """
        pass
    
    def on_enter(self, controller: 'TankController'):
        """Called when entering this substate."""
        opening = self.get_valve_opening()
        controller.bus.publish(config.OPENING_TOPIC, opening=opening)
        logger.info(f"Entered {self.get_state_name().value} - valve: {opening}%")


class NormalSubState(AutomaticSubStateBase):
    """NORMAL: 0% valve opening, monitoring for L1 threshold."""
    
    def get_state_name(self) -> AutomaticStateEnum:
        return AutomaticStateEnum.NORMAL
    
    def get_valve_opening(self) -> float:
        return 0.0
    
    def evaluate_transition(
        self, 
        level: float, 
        elapsed_ms: int
    ) -> Optional[AutomaticSubStateBase]:
        if config.L1_THRESHOLD < level < config.L2_THRESHOLD:
            logger.info(f"L1<{level}<L2 → TRACKING_PRE_ALARM")
            return TrackingPreAlarmSubState()
        elif level >= config.L2_THRESHOLD:
            logger.warning(f"{level}>=L2 → ALARM")
            return AlarmSubState()
        return None


class TrackingPreAlarmSubState(AutomaticSubStateBase):
    """TRACKING_PRE_ALARM: 0% valve, timer T1 for transition to PRE_ALARM."""
    
    def get_state_name(self) -> AutomaticStateEnum:
        return AutomaticStateEnum.TRACKING_PRE_ALARM
    
    def get_valve_opening(self) -> float:
        return 0.0
    
    def evaluate_transition(
        self, 
        level: float, 
        elapsed_ms: int
    ) -> Optional[AutomaticSubStateBase]:
        if level <= config.L1_THRESHOLD:
            logger.info(f"{level}<=L1 → NORMAL")
            return NormalSubState()
        elif level >= config.L2_THRESHOLD:
            logger.warning(f"{level}>=L2 → ALARM")
            return AlarmSubState()
        elif elapsed_ms > config.T1_DURATION * 1000:
            logger.warning(f"T1 timeout → PRE_ALARM")
            return PreAlarmSubState()
        return None


class PreAlarmSubState(AutomaticSubStateBase):
    """PRE_ALARM: 50% valve opening."""
    
    def get_state_name(self) -> AutomaticStateEnum:
        return AutomaticStateEnum.PRE_ALARM
    
    def get_valve_opening(self) -> float:
        return 50.0
    
    def evaluate_transition(
        self, 
        level: float, 
        elapsed_ms: int
    ) -> Optional[AutomaticSubStateBase]:
        if level <= config.L1_THRESHOLD:
            logger.info(f"{level}<=L1 → NORMAL")
            return NormalSubState()
        elif level >= config.L2_THRESHOLD:
            logger.warning(f"{level}>=L2 → ALARM")
            return AlarmSubState()
        return None


class AlarmSubState(AutomaticSubStateBase):
    """ALARM: 100% valve opening (critical level)."""
    
    def get_state_name(self) -> AutomaticStateEnum:
        return AutomaticStateEnum.ALARM
    
    def get_valve_opening(self) -> float:
        return 100.0
    
    def evaluate_transition(
        self, 
        level: float, 
        elapsed_ms: int
    ) -> Optional[AutomaticSubStateBase]:
        if level <= config.L2_THRESHOLD:
            logger.info(f"{level}<=L2 → PRE_ALARM")
            return PreAlarmSubState()
        return None
