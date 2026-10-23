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

    # --- Capability & Cargo Specifications ---
    vehicle_class: Optional[str] = None
    payload_capacity_tonnes: Optional[float] = None
    gross_vehicle_weight_tonnes: Optional[float] = None
    supported_cargo_categories: Optional[list[str]] = None
    body_type: Optional[str] = None
    temperature_controlled: Optional[bool] = False
    hazardous_certified: Optional[bool] = False

    # --- Vehicle Documents ---
    rc_url: Optional[str] = None
    insurance_url: Optional[str] = None
    insurance_expiry: Optional[str] = None
    puc_url: Optional[str] = None
    puc_expiry: Optional[str] = None
    fitness_url: Optional[str] = None
    fitness_expiry: Optional[str] = None
    permit_url: Optional[str] = None
    permit_expiry: Optional[str] = None

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
    vehicle_class: Optional[str] = None
    payload_capacity_tonnes: Optional[float] = None
    gross_vehicle_weight_tonnes: Optional[float] = None
    supported_cargo_categories: Optional[list[str]] = None
    body_type: Optional[str] = None
    temperature_controlled: Optional[bool] = False
    hazardous_certified: Optional[bool] = False


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
    vehicle_class: Optional[str] = None
    payload_capacity_tonnes: Optional[float] = None
    gross_vehicle_weight_tonnes: Optional[float] = None
    supported_cargo_categories: Optional[list[str]] = None
    body_type: Optional[str] = None
    temperature_controlled: Optional[bool] = None
    hazardous_certified: Optional[bool] = None


class VehicleStatusChanged(BaseModel):
    status: VehicleStatus
