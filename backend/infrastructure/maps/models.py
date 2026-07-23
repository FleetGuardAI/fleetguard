"""
Maps Service - Models
"""

from typing import Dict, Any, Optional, List
import uuid
from pydantic import BaseModel, Field

class Coordinate(BaseModel):
    latitude: float
    longitude: float

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }

class Address(BaseModel):
    formatted_address: str
    locality: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }

class Route(BaseModel):
    origin: Coordinate
    destination: Coordinate
    distance_meters: int
    duration_seconds: int
    polyline: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }

class Geofence(BaseModel):
    geofence_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    center: Coordinate
    radius_meters: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
