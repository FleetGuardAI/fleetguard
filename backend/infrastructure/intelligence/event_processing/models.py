"""
Fleet Intelligence Engine - Event Processing Models
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, Literal
from pydantic import BaseModel, Field


class BaseOperationalEvent(BaseModel):
    """
    Base model for raw operational events from external systems.
    Events are strictly immutable facts.
    """
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    correlation_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class FuelReceiptEvent(BaseOperationalEvent):
    event_type: Literal["fuel_receipt"] = "fuel_receipt"
    quantity: float
    amount: float
    station_name: Optional[str] = None
    station_lat: Optional[float] = None
    station_lon: Optional[float] = None


class GPSEvent(BaseOperationalEvent):
    event_type: Literal["gps"] = "gps"
    latitude: float
    longitude: float
    accuracy: float


class FuelSensorEvent(BaseOperationalEvent):
    event_type: Literal["fuel_sensor"] = "fuel_sensor"
    fuel_before: float
    fuel_after: float


class VehicleSnapshotEvent(BaseOperationalEvent):
    event_type: Literal["vehicle_snapshot"] = "vehicle_snapshot"
    vehicle_id: str
    tank_capacity: float
