"""
Vehicle Management Domain - Service
"""

import uuid
from typing import List, Optional, Tuple
from domain.vehicle.models import Vehicle, VehicleStatus, VehicleConfiguration, VehicleSpecification
from domain.vehicle.value_objects import RegistrationNumber, VIN, EngineNumber, ChassisNumber
from domain.vehicle.aggregate import VehicleAggregate
from domain.vehicle.repository import BaseVehicleRepository
from domain.vehicle.schemas import RegisterVehicleRequest
from domain.vehicle.errors import DuplicateRegistration, VehicleNotFound
from domain.vehicle.events import DomainEvent

class VehicleService:
    def __init__(self, repository: BaseVehicleRepository):
        self.repository = repository
        
    def register_vehicle(self, request: RegisterVehicleRequest) -> Tuple[Vehicle, List[DomainEvent]]:
        if self.repository.find_by_registration(request.registration_number):
            raise DuplicateRegistration(f"Registration number {request.registration_number} is already in use.")
            
        vehicle = Vehicle(
            registration_number=RegistrationNumber(value=request.registration_number),
            vin=VIN(value=request.vin) if request.vin else None,
            chassis_number=ChassisNumber(value=request.chassis_number) if request.chassis_number else None,
            engine_number=EngineNumber(value=request.engine_number) if request.engine_number else None,
            make=request.make,
            model=request.model,
            manufacturing_year=request.manufacturing_year,
            category=request.category,
            fuel_type=request.fuel_type,
            ownership_type=request.ownership_type,
            organization_id=request.organization_id,
            metadata=request.metadata
        )
        
        registered_vehicle, events = VehicleAggregate.register_vehicle(vehicle)
        self.repository.create(registered_vehicle)
        return registered_vehicle, events

    def activate_vehicle(self, vehicle_id: uuid.UUID, reason: Optional[str] = None) -> Tuple[Vehicle, List[DomainEvent]]:
        vehicle = self.repository.find_by_id(vehicle_id)
        if not vehicle:
            raise VehicleNotFound(f"Vehicle {vehicle_id} not found.")
            
        updated, events = VehicleAggregate.activate_vehicle(vehicle, reason)
        self.repository.update(updated)
        return updated, events

    def update_configuration(self, vehicle_id: uuid.UUID, config: VehicleConfiguration) -> Tuple[Vehicle, List[DomainEvent]]:
        vehicle = self.repository.find_by_id(vehicle_id)
        if not vehicle:
            raise VehicleNotFound(f"Vehicle {vehicle_id} not found.")
            
        updated, events = VehicleAggregate.update_configuration(vehicle, config)
        self.repository.update(updated)
        return updated, events

    def get_vehicle(self, vehicle_id: uuid.UUID) -> Optional[Vehicle]:
        return self.repository.find_by_id(vehicle_id)
