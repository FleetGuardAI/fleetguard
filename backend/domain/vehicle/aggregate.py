"""
Vehicle Management Domain - Aggregate Root
"""

import uuid
from typing import List, Tuple, Optional
from domain.vehicle.models import Vehicle, VehicleStatus, VehicleSpecification, VehicleConfiguration
from domain.vehicle.events import (
    DomainEvent,
    VehicleRegistered,
    VehicleActivated,
    VehicleDeactivated,
    VehicleArchived,
    VehicleRetired,
    VehicleSpecificationChanged,
    VehicleConfigurationChanged
)
from domain.vehicle.errors import InvalidVehicleState
from domain.vehicle.validators import validate_manufacturing_year


class VehicleAggregate:
    """
    Enforces domain invariants and coordinates state transitions.
    """
    
    @classmethod
    def register_vehicle(cls, vehicle: Vehicle) -> Tuple[Vehicle, List[DomainEvent]]:
        """
        Creates a new vehicle and registers its creation event.
        """
        validate_manufacturing_year(vehicle.manufacturing_year)
        
        # Initial status must be INACTIVE
        if vehicle.status != VehicleStatus.INACTIVE:
            raise InvalidVehicleState("New vehicles must be registered as INACTIVE.")
            
        event = VehicleRegistered(
            vehicle_id=vehicle.vehicle_id,
            registration_number=vehicle.registration_number.value,
            organization_id=vehicle.organization_id,
            metadata=vehicle.metadata
        )
        return vehicle, [event]

    @classmethod
    def activate_vehicle(cls, vehicle: Vehicle, reason: Optional[str] = None) -> Tuple[Vehicle, List[DomainEvent]]:
        if vehicle.status == VehicleStatus.ARCHIVED:
            raise InvalidVehicleState("Cannot activate an archived vehicle directly.")
        if vehicle.status == VehicleStatus.ACTIVE:
            return vehicle, []
            
        updated = vehicle.model_copy(update={"status": VehicleStatus.ACTIVE})
        event = VehicleActivated(vehicle_id=vehicle.vehicle_id, reason=reason)
        return updated, [event]

    @classmethod
    def deactivate_vehicle(cls, vehicle: Vehicle, reason: Optional[str] = None) -> Tuple[Vehicle, List[DomainEvent]]:
        if vehicle.status in (VehicleStatus.ARCHIVED, VehicleStatus.RETIRED):
            raise InvalidVehicleState("Cannot deactivate an archived or retired vehicle.")
        if vehicle.status == VehicleStatus.INACTIVE:
            return vehicle, []
            
        updated = vehicle.model_copy(update={"status": VehicleStatus.INACTIVE})
        event = VehicleDeactivated(vehicle_id=vehicle.vehicle_id, reason=reason)
        return updated, [event]

    @classmethod
    def archive_vehicle(cls, vehicle: Vehicle, reason: Optional[str] = None) -> Tuple[Vehicle, List[DomainEvent]]:
        if vehicle.status == VehicleStatus.ARCHIVED:
            return vehicle, []
            
        updated = vehicle.model_copy(update={"status": VehicleStatus.ARCHIVED})
        event = VehicleArchived(vehicle_id=vehicle.vehicle_id, reason=reason)
        return updated, [event]

    @classmethod
    def retire_vehicle(cls, vehicle: Vehicle, reason: Optional[str] = None) -> Tuple[Vehicle, List[DomainEvent]]:
        if vehicle.status == VehicleStatus.RETIRED:
            return vehicle, []
            
        updated = vehicle.model_copy(update={"status": VehicleStatus.RETIRED})
        event = VehicleRetired(vehicle_id=vehicle.vehicle_id, reason=reason)
        return updated, [event]

    @classmethod
    def update_configuration(cls, vehicle: Vehicle, configuration: VehicleConfiguration) -> Tuple[Vehicle, List[DomainEvent]]:
        if vehicle.status == VehicleStatus.RETIRED:
            raise InvalidVehicleState("Cannot update configuration for a retired vehicle.")
            
        updated = vehicle.model_copy(update={"configuration": configuration})
        event = VehicleConfigurationChanged(vehicle_id=vehicle.vehicle_id)
        return updated, [event]
        
    @classmethod
    def update_specification(cls, vehicle: Vehicle, specification: VehicleSpecification) -> Tuple[Vehicle, List[DomainEvent]]:
        if vehicle.status == VehicleStatus.RETIRED:
            raise InvalidVehicleState("Cannot update specification for a retired vehicle.")
            
        updated = vehicle.model_copy(update={"specification": specification})
        event = VehicleSpecificationChanged(vehicle_id=vehicle.vehicle_id)
        return updated, [event]
