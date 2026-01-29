from typing import Dict, Any, List
from .base_controller import BaseController
from services.base_service import BaseService
from services.event_dispatcher import EventDispatcher
from models.schemas import ModeRequest, ValveRequest, StatusResponse, Mode, SystemState
from utils.logger import get_logger

logger = get_logger(__name__)


class MockController(BaseController):
    """
    Mock controller for testing purposes.
    
    Provides simple, predictable responses without complex business logic.
    Can work with any combination of services.
    """

    def __init__(
        self,
        services: List[BaseService],
        event_dispatcher: EventDispatcher,
        configure_fn=None
    ):
        """
        Initialize mock controller.
        
        Args:
            services: List of services to manage
            event_dispatcher: Event dispatcher
            configure_fn: Optional function to configure services
                         Signature: configure_fn(controller, services, dispatcher)
        """
        self._mock_status = "healthy"
        self._mock_mode = Mode.AUTOMATIC
        self._mock_valve = 0.0
        self._mock_readings = []
        
        # Apply custom configuration if provided
        if configure_fn:
            configure_fn(self, services, event_dispatcher)
        
        super().__init__(services, event_dispatcher)
        logger.info("MockController initialized")
    
    # -------------------- Mock Methods --------------------
    
    def on_mock_data(self, data: Any) -> None:
        """Generic mock data handler."""
        logger.info(f"MockController received data: {data}")
        self._mock_readings.append({"data": data})
    
    async def get_status(self) -> StatusResponse:
        """Return mock status."""
        return StatusResponse(
            state=SystemState.AUTOMATIC,
            mode=self._mock_mode,
            valve_opening=self._mock_valve,
            water_level=50.0,
            timestamp=None
        )
    
    async def get_readings(self, limit: int = 60) -> list[Dict[str, Any]]:
        """Return mock readings."""
        return self._mock_readings[-limit:]
    
    async def set_mode(self, req: ModeRequest) -> Dict[str, str]:
        """Mock set mode."""
        logger.info(f"MockController set mode to {req.mode}")
        self._mock_mode = req.mode
        return {"result": "ok"}
    
    async def set_valve(self, req: ValveRequest) -> Dict[str, str]:
        """Mock set valve."""
        logger.info(f"MockController set valve to {req.opening}%")
        self._mock_valve = req.opening
        return {"result": "ok"}
    
    async def health_check(self) -> Dict[str, str]:
        """Mock health check."""
        return {"status": self._mock_status}
