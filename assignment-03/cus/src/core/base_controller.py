from abc import ABC, abstractmethod
from typing import List, Dict
from api.schemas import Mode, Status


class BaseController(ABC):
    @abstractmethod
    def get_status(self) -> Status:
        """
        Get the current system status.
        
        :param self: The instance of the controller.
        :return: Current system status
        :rtype: Status
        """
        pass

    @abstractmethod
    def get_mode(self) -> Mode:
        pass

    @abstractmethod
    def get_valve_opening(self) -> float:
        pass

    @abstractmethod
    def get_readings(self, limit: int = 60) -> List[Dict]:
        """Return latest readings as list of { ts, value } items."""
        pass

    @abstractmethod
    def set_mode(self, mode: Mode):
        pass

    @abstractmethod
    def is_manual(self) -> bool:
        pass

    @abstractmethod
    def set_valve(self, percentage: float):
        pass

    @abstractmethod
    def manual_valve(self, opening):
        pass