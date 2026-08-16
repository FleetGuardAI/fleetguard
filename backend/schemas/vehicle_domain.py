"""
FleetGuard — Vehicle Domain Schemas
Defines value objects for vehicle operations and read-models for API responses.
"""

from typing import Optional
from pydantic import BaseModel, Field
from models.vehicle_domain import VehicleStatus


# ===========================================================================
# Read Models
# ===========================================================================

class VehicleResponse(BaseModel):
    id: int
    registration_number: str
    vin: Optional[str] = None
    engine_number: Optional[str] = None
    make: str
    model: Optional[str] = None
    year: Optional[int] = None
    tank_capacity: float
    status: VehicleStatus
    ownership_info: Optional[str] = None
    origin_type: Optional[str] = None
    origin_id: Optional[str] = None
    assigned_driver_id: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


# ===========================================================================
# Write Models / Commands
# ===========================================================================

class VehicleCreate(BaseModel):
    license_plate: Optional[str] = Field(None, description="Registration license plate")
    registration_number: Optional[str] = Field(None, description="Registration number")
    make: str = Field(..., description="Manufacturer make")
    model: Optional[str] = None
    year: Optional[int] = None
    vin: Optional[str] = None
    engine_number: Optional[str] = None
    tank_capacity: Optional[float] = 400.0


class VehicleRegistered(BaseModel):
    registration_number: str
    vin: Optional[str] = None
    make: str
    model: Optional[str] = None


class VehicleUpdated(BaseModel):
    license_plate: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    tank_capacity: Optional[float] = None
    ownership_info: Optional[str] = None
    driver_id: Optional[int] = None


class VehicleStatusChanged(BaseModel):
    status: VehicleStatus
