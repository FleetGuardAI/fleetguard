"""
Trip Management Domain - Events
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class DomainEvent(BaseModel):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_config = {"frozen": True}

class TripCreated(DomainEvent):
    trip_id: uuid.UUID
    vehicle_id: str
    organization_id: uuid.UUID

class TripStarted(DomainEvent):
    trip_id: uuid.UUID
    started_at: datetime
    origin_latitude: float
    origin_longitude: float

class TripPaused(DomainEvent):
    trip_id: uuid.UUID

class TripResumed(DomainEvent):
    trip_id: uuid.UUID

class TripCompleted(DomainEvent):
    trip_id: uuid.UUID
    ended_at: datetime
    destination_latitude: float
    destination_longitude: float
    total_distance_km: float

class TripCancelled(DomainEvent):
    trip_id: uuid.UUID
    reason: Optional[str] = None
