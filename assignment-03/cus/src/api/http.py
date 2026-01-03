from utils.logger import get_logger
from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
from core.base_controller import BaseController
from api.schemas import (
    Mode,
    ModeRequest,
    ValveRequest,
    StatusResponse
)

logger = get_logger(__name__)


def create_app(controller: BaseController) -> FastAPI:
    """
    FastAPI application factory.
    Acts as the HTTP adapter (API Gateway) for the CUS subsystem.
    """

    app = FastAPI(
        title="Control Unit Subsystem API",
        description="REST API for the Smart Tank Monitoring System",
        version="1.0.0",
    )

    # Allow requests from the static client served on localhost:8080
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:8080"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    router = APIRouter(prefix="/api")

    # -----------------------------
    # GET /readings
    # -----------------------------
    @router.get("/readings")
    async def get_readings(limit: int = 60) -> List[Dict]:
        """
        Return latest readings. Each item: { "ts": <timestamp>, "value": <number> }
        """
        try:
            logger.debug(f"Fetching {limit} readings")
            return controller.get_readings(limit)
        except Exception as e:
            logger.error(f"Failed to get readings: {e}")
            return []

    # -----------------------------
    # GET /status
    # -----------------------------
    @router.get("/status", response_model=StatusResponse)
    async def get_status():
        """
        Returns the current system status including mode and valve opening.
        """
        logger.debug("Status requested")
        return {
            "status": controller.get_status(),
            "mode": controller.get_mode(),
            "valve_opening": controller.get_valve_opening()
        }

    # -----------------------------
    # POST /mode
    # -----------------------------
    @router.post("/mode")
    async def set_mode(req: ModeRequest) -> Dict[str, str]:
        """
        Switch system mode: AUTOMATIC or MANUAL.
        """
        try:
            logger.info(f"Setting mode to {req.mode}")
            controller.set_mode(Mode(req.mode))
        except ValueError:
            logger.warning(f"Invalid mode requested: {req.mode}")
            raise HTTPException(status_code=400, detail="Invalid mode")

        return {"result": "ok"}

    # -----------------------------
    # POST /valve
    # -----------------------------
    @router.post("/valve")
    async def set_valve(req: ValveRequest) -> Dict[str, str]:
        """
        Manually set valve opening percentage.
        Allowed only in MANUAL mode.
        """
        if not controller.is_manual():
            logger.warning("Valve setting attempted while not in MANUAL mode")
            raise HTTPException(
                status_code=409,
                detail="System not in MANUAL mode"
            )

        if not (0 <= req.opening <= 100):
            logger.warning(f"Invalid valve opening value: {req.opening}")
            raise HTTPException(
                status_code=400,
                detail="Valve opening must be between 0 and 100"
            )

        logger.info(f"Setting valve opening to {req.opening}%")
        controller.manual_valve(req.opening)
        return {"result": "ok"}

    # -----------------------------
    # GET /health
    # -----------------------------
    @router.get("/health")
    async def health_check():
        """
        Simple health check endpoint.
        """
        return {"status": "alive"}

    app.include_router(router)

    return app