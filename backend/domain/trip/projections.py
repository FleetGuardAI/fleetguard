"""
Trip Management Domain - Projections
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from domain.trip.models import TripStatus

class TripSummary(BaseModel):
    trip_id: uuid.UUID
    vehicle_id: str
    status: TripStatus
    started_at: Optional[datetime] = None
    total_distance_km: float

class ActiveTripSummary(TripSummary):
    pass

class VehicleTripSummary(TripSummary):
    pass

class DriverTripSummary(TripSummary):
    driver_assignment_id: Optional[uuid.UUID] = None
