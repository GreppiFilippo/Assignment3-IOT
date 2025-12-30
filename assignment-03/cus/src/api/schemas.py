from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Mode(str, Enum):
    AUTOMATIC = "AUTOMATIC"
    MANUAL = "MANUAL"


class SystemState(str, Enum):
    AUTOMATIC = "AUTOMATIC"
    MANUAL = "MANUAL"
    UNCONNECTED = "UNCONNECTED"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class Status(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ModeRequest(BaseModel):
    """Request model to change system mode."""
    mode: Mode


class ValveRequest(BaseModel):
    """Request model to set manual valve opening (percentage)."""
    opening: float = Field(..., ge=0, le=100, description="Opening percentage (0-100)")


class LevelReading(BaseModel):
    """Single water level reading with timestamp."""
    water_level: float
    timestamp: datetime


class StatusResponse(BaseModel):
    """Response model for system status."""
    status: Status
    # logical/system state (AUTOMATIC, MANUAL, UNCONNECTED, NOT_AVAILABLE)
    state: Optional[SystemState] = None
    mode: Optional[Mode] = None
    # valve opening percentage (0-100)
    valve_opening: Optional[float] = Field(None, ge=0, le=100)
    # optional latest water level and timestamp for dashboard
    water_level: Optional[float] = None
    timestamp: Optional[datetime] = None