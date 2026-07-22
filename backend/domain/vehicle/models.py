"""
Vehicle Management Domain - Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from domain.vehicle.value_objects import RegistrationNumber, VIN, EngineNumber, ChassisNumber


class VehicleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    RETIRED = "RETIRED"
    ARCHIVED = "ARCHIVED"


class FuelType(str, Enum):
    DIESEL = "DIESEL"
    PETROL = "PETROL"
    CNG = "CNG"
    LNG = "LNG"
    ELECTRIC = "ELECTRIC"
    HYBRID = "HYBRID"
    UNKNOWN = "UNKNOWN"


class VehicleCategory(str, Enum):
    TRUCK = "TRUCK"
    TRAILER = "TRAILER"
    TANKER = "TANKER"
    TIPPER = "TIPPER"
    LCV = "LCV"
    HCV = "HCV"
    OTHER = "OTHER"


class OwnershipType(str, Enum):
    OWNED = "OWNED"
    LEASED = "LEASED"
    RENTED = "RENTED"


class VehicleSpecification(BaseModel):
    """
    Physical characteristics of the vehicle.
    """
    fuel_tank_capacity: float = 0.0
    tyre_count: int = 4
    axle_count: int = 2
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}


class VehicleConfiguration(BaseModel):
    """
    Operational settings for the vehicle.
    """
    average_expected_mileage: float = 0.0
    odometer_unit: str = "km"
    notification_preferences: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}


class Vehicle(BaseModel):
    """
    Immutable representation of a Vehicle entity.
    Mutable state transitions should be done via creating a new copy.
    """
    vehicle_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    registration_number: RegistrationNumber
    vin: Optional[VIN] = None
    chassis_number: Optional[ChassisNumber] = None
    engine_number: Optional[EngineNumber] = None
    make: str
    model: str
    manufacturing_year: int
    category: VehicleCategory
    fuel_type: FuelType
    ownership_type: OwnershipType
    status: VehicleStatus = VehicleStatus.INACTIVE
    organization_id: uuid.UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    specification: VehicleSpecification = Field(default_factory=VehicleSpecification)
    configuration: VehicleConfiguration = Field(default_factory=VehicleConfiguration)

    model_config = {"frozen": True, "extra": "forbid"}
