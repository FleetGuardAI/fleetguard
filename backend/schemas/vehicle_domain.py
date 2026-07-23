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

    model_config = {
        "from_attributes": True
    }


# ===========================================================================
# Value Objects / Internal Commands
# ===========================================================================

class VehicleRegistered(BaseModel):
    registration_number: str
    vin: Optional[str] = None
    make: str
    model: Optional[str] = None


class VehicleUpdated(BaseModel):
    tank_capacity: Optional[float] = None
    ownership_info: Optional[str] = None


class VehicleStatusChanged(BaseModel):
    status: VehicleStatus
