"""
Vehicle Management Domain - Schemas
"""

import uuid
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from domain.vehicle.models import VehicleCategory, FuelType, OwnershipType, VehicleStatus, VehicleSpecification, VehicleConfiguration

class RegisterVehicleRequest(BaseModel):
    registration_number: str
    organization_id: uuid.UUID
    make: str
    model: str
    manufacturing_year: int
    category: VehicleCategory
    fuel_type: FuelType
    ownership_type: OwnershipType
    vin: Optional[str] = None
    chassis_number: Optional[str] = None
    engine_number: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class UpdateConfigurationRequest(BaseModel):
    configuration: VehicleConfiguration
    
class UpdateSpecificationRequest(BaseModel):
    specification: VehicleSpecification
    
class StateChangeRequest(BaseModel):
    reason: Optional[str] = None

class VehicleResponse(BaseModel):
    vehicle_id: uuid.UUID
    registration_number: str
    make: str
    model: str
    status: VehicleStatus
    # A full response would include all fields, simplified for mapping here
    
    @classmethod
    def from_domain(cls, vehicle):
        return cls(
            vehicle_id=vehicle.vehicle_id,
            registration_number=vehicle.registration_number.value,
            make=vehicle.make,
            model=vehicle.model,
            status=vehicle.status
        )
