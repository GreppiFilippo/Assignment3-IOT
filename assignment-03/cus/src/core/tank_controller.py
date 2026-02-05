import asyncio
import time
from services.base_service import BaseService
from services.event_bus import EventBus
from models.schemas import SystemState, AutomaticState
import config

class TankController(BaseService):
    """Core Controller for Tank System."""

    def __init__(self, event_bus: EventBus):
        super().__init__("tank_controller", event_bus)
        self.water_level: float = 0.0
        self.set_system_state(SystemState.UNCONNECTED)
        self.set_automatic_state(AutomaticState.NORMAL)
        self.valve_opening: float = 0.0
        self.change = False
        self.last_level_timestamp: int = 0

    async def run(self):
        """Main execution loop for the Tank Controller."""
        while self._running:
            match self.model.state:
                case SystemState.UNCONNECTED:
                    if self.check_and_set_just_entered_system_state():
                        self.event_bus.publish(config.MODE, SystemState.UNCONNECTED)
                case SystemState.AUTOMATIC:
                    match self.model.automatic_state:
                        case AutomaticState.NORMAL:
                            if self.check_and_set_just_entered_automatic_state():
                                self.event_bus.publish(config.MODE, SystemState.AUTOMATIC)
                            if self.model.valve_opening  > config.L1_THRESHOLD and self.model.valve_opening  < config.L2_THRESHOLD:
                                self.set_automatic_state(AutomaticState.TRACKING_PRE_ALARM)
                        case AutomaticState.TRACKING_PRE_ALARM:
                            if self.elapsed_time_in_automatic_state() > config.T1_DURATION * 1000:
                                self.set_automatic_state(AutomaticState.PRE_ALARM)
                            if self.model.valve_opening  <= config.L1_THRESHOLD:
                                self.set_automatic_state(AutomaticState.NORMAL)
                            if self.model.valve_opening  >= config.L2_THRESHOLD:
                                self.set_automatic_state(AutomaticState.ALARM)
                        case AutomaticState.PRE_ALARM:
                            if self.check_and_set_just_entered_automatic_state():
                                self.model.valve_opening = 50.0
                            if self.model.valve_opening  > config.L2_THRESHOLD:
                                self.set_automatic_state(AutomaticState.ALARM)
                            if self.model.valve_opening  <= config.L1_THRESHOLD:
                                self.set_automatic_state(AutomaticState.NORMAL)
                        case AutomaticState.ALARM:
                            if self.check_and_set_just_entered_automatic_state():
                                self.model.valve_opening = 100.0
                            if self.model.valve_opening  <= config.L2_THRESHOLD:
                                self.set_automatic_state(AutomaticState.PRE_ALARM)
                    if self.button:
                        self.set_system_state(SystemState.MANUAL)
                        self.button = False
                    if time.monotonic() * 1000 - self.last_level_timestamp > config.LEVEL_TIMEOUT * 1000:
                        self.set_system_state(SystemState.UNCONNECTED)
                case SystemState.MANUAL:
                    self.check_and_set_just_entered_system_state()
                    if self.button:
                        self.set_system_state(SystemState.AUTOMATIC)
                        self.button = False
                    if time.monotonic() * 1000 - self.last_level_timestamp > config.LEVEL_TIMEOUT * 1000:
                        self.set_system_state(SystemState.UNCONNECTED)
            await asyncio.sleep(0.1)

    def set_change(self):
        """Change mode"""
        self.change = True

    def set_valve_opening(self, opening: float):
        """Set valve opening percentage."""
        self.valve_opening = opening

    def set_water_level(self, level: float):
        """Set current water level."""
        self.water_level = level
        self.last_level_timestamp = int(time.monotonic() * 1000)

    # State-management helpers similar to DroneTask
    def set_system_state(self, state: SystemState):
        self._system_state = state
        self._system_state_timestamp = int(time.monotonic() * 1000)
        self.set_automatic_state(AutomaticState.NORMAL)
        self._system_just_entered = True

    def elapsed_time_in_system_state(self) -> int:
        return int(time.monotonic() * 1000) - getattr(self, "_system_state_timestamp", 0)

    def check_and_set_just_entered_system_state(self) -> bool:
        bak = bool(getattr(self, "_system_just_entered", False))
        if bak:
            self._system_just_entered = False
        return bak

    def set_automatic_state(self, state: AutomaticState):
        self._automatic_state = state
        self._automatic_state_timestamp = int(time.monotonic() * 1000)
        self._automatic_just_entered = True

    def elapsed_time_in_automatic_state(self) -> int:
        return int(time.monotonic() * 1000) - getattr(self, "_automatic_state_timestamp", 0)

    def check_and_set_just_entered_automatic_state(self) -> bool:
        bak = bool(getattr(self, "_automatic_just_entered", False))
        if bak:
            self._automatic_just_entered = False
        return bak

    


