"""
FleetGuard — Trip Domain Pydantic Schemas
Defines value objects for trip operations and read-models for API responses.
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
from models.trip_domain import TripStatus


# ===========================================================================
# Read Models
# ===========================================================================

class TripResponse(BaseModel):
    id: int
    trip_id: str
    status: TripStatus
    
    # --- Locations ---
    origin_location: Optional[str] = None
    destination_location: Optional[str] = None

    # --- Distance ---
    planned_distance: Optional[float] = None
    actual_distance: Optional[float] = None

    # --- Timing ---
    planned_start_time: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    planned_end_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None

    # --- Assignments ---
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None

    # --- Financial ---
    revenue: Optional[float] = None
    planned_cost: Optional[float] = None
    planned_fuel_liters: Optional[float] = None
    cargo_weight: Optional[float] = None
    
    origin_type: Optional[str] = None
    origin_id: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


# ===========================================================================
# Write Models / Commands
# ===========================================================================

class TripCreate(BaseModel):
    vehicle_id: int
    driver_id: int
    origin_location: str
    destination_location: str
    planned_distance: Optional[float] = None
    planned_start_time: Optional[datetime] = None
    planned_end_time: Optional[datetime] = None

class TripUpdated(BaseModel):
    status: Optional[TripStatus] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None

class TripCreated(BaseModel):
    trip_id: str
    origin_location: Optional[str] = None
    destination_location: Optional[str] = None
    planned_distance: Optional[float] = None
    planned_start_time: Optional[datetime] = None
    planned_end_time: Optional[datetime] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None


class TripStarted(BaseModel):
    actual_start_time: Optional[datetime] = None


class TripPaused(BaseModel):
    pass


class TripResumed(BaseModel):
    pass


class TripCompleted(BaseModel):
    actual_end_time: Optional[datetime] = None
    actual_distance: Optional[float] = None


class TripCancelled(BaseModel):
    pass


class TripDriverAssigned(BaseModel):
    driver_id: int


class TripVehicleAssigned(BaseModel):
    vehicle_id: int
