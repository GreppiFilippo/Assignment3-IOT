from datetime import datetime
from random import random
from core.base_controller import BaseController, Mode, Status
import datetime
import random


class MockController(BaseController):
    """Mock controller for development and testing."""
    def __init__(self):
        super().__init__()
        self._mode = Mode.MANUAL
        self._valve = 40.5
        self._level = None
        self._status = Status.OK

    def get_status(self) -> Status:
        return self._status

    def get_mode(self) -> Mode:
        return self._mode

    def get_valve_opening(self) -> float:
        return float(self._valve)

    def get_readings(self, limit: int = 60):
        """Return synthetic readings for testing the UI.

        Each item is a dict with `ts` (ISO timestamp) and `value` (float).
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        readings = []
        for i in range(limit):
            ts = (now - datetime.timedelta(seconds=(limit - i) * 2)).isoformat()
            value = round(20 + 10 * random.random(), 2)
            readings.append({"ts": ts, "value": value})
        return readings

    def set_mode(self, mode):
        self._mode = mode

    def is_manual(self) -> bool:
        return self._mode == Mode.MANUAL

    def set_valve(self, percentage: float):
        self._valve = percentage

    def manual_valve(self, opening):
        self._valve = opening
