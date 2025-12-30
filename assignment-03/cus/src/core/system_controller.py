from typing import Dict, List
from src.api.schemas import Mode, Status
from src.core.base_controller import BaseController


class SystemController(BaseController):
    """Implementation of the BaseController for system management."""

    def __init__(self) -> None:
        super().__init__()

    def get_status(self) -> Status:
        raise NotImplementedError

    def get_mode(self) -> Mode:
        raise NotImplementedError

    def get_valve_opening(self) -> float:
        raise NotImplementedError

    def get_readings(self, limit: int = 60) -> List[Dict]:
        raise NotImplementedError

    def set_mode(self, mode: Mode):
        raise NotImplementedError

    def is_manual(self) -> bool:
        raise NotImplementedError

    def set_valve(self, percentage: float):
        raise NotImplementedError

    def manual_valve(self, opening):
        raise NotImplementedError
