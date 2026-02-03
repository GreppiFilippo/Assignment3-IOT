from collections import deque
from typing import Deque, Optional

from .schemas import LevelReading, SystemState


class SystemModel:
    """
    Model for the system state and level readings.

    Single Source of Truth for the whole system.
    
    This model is used to store the current state and level readings of the system.
    It also provides utility methods for accessing and manipulating the data.
    """
    def __init__(self, max_history: int = 100):
        self._state: SystemState = SystemState.AUTOMATIC
        self._level_reading: Deque[LevelReading] = deque(maxlen=max_history)
        self._valve_opening: float = 0.0

    # ---- STATE ----
    @property
    def state(self) -> SystemState:
        return self._state

    @state.setter
    def state(self, value: SystemState):
        self._state = value

    # ---- LEVEL READINGS ----
    def add_level_reading(self, reading: LevelReading):
        self._level_reading.append(reading)

    def get_level_readings(self) -> list[LevelReading]:
        return list(self._level_reading)

    def get_last_level_reading(self) -> Optional[LevelReading]:
        return self._level_reading[-1] if self._level_reading else None

    def erase_level_readings(self, from_index: int = 0, to_index: Optional[int] = None):
        self._level_reading = deque(list(self._level_reading)[from_index:to_index], maxlen=self._level_reading.maxlen)

    def clear_level_readings(self):
        self._level_reading.clear()

    # ---- VALVE OPENING ----
    @property
    def valve_opening(self) -> float:
        return self._valve_opening

    @valve_opening.setter
    def valve_opening(self, value: float):
        self._valve_opening = value

    # ---- UTILITY ----
    def last_value(self) -> Optional[float]:
        """Return the last measured value, if available."""
        last = self.get_last_level_reading()
        return last.water_level if last else None
