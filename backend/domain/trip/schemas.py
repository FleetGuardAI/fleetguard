"""
Trip Management Domain - Schemas
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel

from domain.trip.models import TripStatus
from domain.trip.value_objects import Location, Distance, Duration

# Note: We ONLY define response schemas. Trip creation is Event-Driven.

class LocationSchema(BaseModel):
    latitude: float
    longitude: float
    address: Optional[str] = None

class TripResponse(BaseModel):
    trip_id: uuid.UUID
    organization_id: uuid.UUID
    vehicle_id: str
    driver_assignment_id: Optional[uuid.UUID] = None
    status: TripStatus
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    origin: Optional[LocationSchema] = None
    destination: Optional[LocationSchema] = None
    total_distance_km: float
    driving_duration_seconds: int
    idle_duration_seconds: int
    stop_count: int
    metadata: Dict[str, Any]

class TripSummaryResponse(BaseModel):
    trip_id: uuid.UUID
    vehicle_id: str
    status: TripStatus
    started_at: Optional[datetime] = None
    total_distance_km: float
