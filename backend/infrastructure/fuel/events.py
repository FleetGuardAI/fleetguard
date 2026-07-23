"""
Fuel Sensor Gateway Framework - Operational Events
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from infrastructure.fuel.models import MeasurementUnit, TelemetryQuality


class BaseFuelEvent(BaseModel):
    """
    Base immutable event representing a fuel observation.
    """
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    device_id: str
    provider: str
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class FuelLevelRecorded(BaseFuelEvent):
    """
    Event emitted when a valid fuel reading is received.
    """
    fuel_level: float
    measurement_unit: MeasurementUnit
    quality: TelemetryQuality
    temperature: Optional[float] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SensorStatusChanged(BaseFuelEvent):
    """
    Event emitted when a sensor health status change is detected.
    """
    sensor_health: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
