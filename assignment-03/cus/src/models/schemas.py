from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class SystemState(str, Enum):
    """
    The current state of the system.
    """
    AUTOMATIC = "AUTOMATIC"
    MANUAL = "MANUAL"
    UNCONNECTED = "UNCONNECTED"

class AutomaticState(str, Enum):
    """
    Sub-states when in AUTOMATIC mode.
    """
    NORMAL = "NORMAL"
    TRACKING_PRE_ALARM = "TRACKING_PRE_ALARM"
    PRE_ALARM = "PRE_ALARM"
    ALARM = "ALARM"


class ValveRequest(BaseModel):
    """
    Request to set the valve opening percentage.
    """
    opening: float = Field(..., ge=0, le=100, description="Opening percentage (0-100)")


class TankLevelPayload(BaseModel):
    """
    MQTT payload for tank/level topic.
    """
    level: float = Field(..., description="Water level in cm")
    timestamp: int = Field(..., description="Timestamp in milliseconds")
    
    def to_datetime(self) -> datetime:
        """Convert timestamp to datetime object"""
        return datetime.fromtimestamp(self.timestamp / 1000.0)


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
    valve_opening: Optional[float] = Field(None, ge=0, le=100)
    water_level: Optional[float] = None
    timestamp: Optional[datetime] = None
