from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Mode(str, Enum):
    """
    The operating mode of the system.
    """
    AUTOMATIC = "AUTOMATIC"
    MANUAL = "MANUAL"


class SystemState(str, Enum):
    """
    The current state of the system.
    """
    AUTOMATIC = "AUTOMATIC"
    MANUAL = "MANUAL"
    UNCONNECTED = "UNCONNECTED"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class ModeRequest(BaseModel):
    """
    Request to change the operating mode of the system.
    """
    mode: Mode


class ValveRequest(BaseModel):
    """
    Request to set the valve opening percentage.
    """
    opening: float = Field(..., ge=0, le=100, description="Opening percentage (0-100)")


class LevelReading(BaseModel):
    """
    Water level reading from the sensor.
    """
    water_level: float
    timestamp: datetime


class StatusResponse(BaseModel):
    """
    Current status of the system.
    """
    state: SystemState
    mode: Mode
    valve_opening: Optional[float] = Field(None, ge=0, le=100)
    water_level: Optional[float] = None
    timestamp: Optional[datetime] = None
