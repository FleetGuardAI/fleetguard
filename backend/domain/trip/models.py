"""
Trip Management Domain - Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from domain.trip.value_objects import TripId, Location, Distance, Duration

class TripStatus(str, Enum):
    CREATED = "CREATED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class Trip(BaseModel):
    """
    Immutable representation of a Trip entity.
    Mutable state transitions should be done via creating a new copy.
    """
    trip_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    organization_id: uuid.UUID
    vehicle_id: str
    driver_assignment_id: Optional[uuid.UUID] = None
    
    status: TripStatus = TripStatus.CREATED
    
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    origin: Optional[Location] = None
    destination: Optional[Location] = None
    
    total_distance: Distance = Field(default_factory=Distance)
    driving_duration: Duration = Field(default_factory=Duration)
    idle_duration: Duration = Field(default_factory=Duration)
    stop_count: int = 0
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}
