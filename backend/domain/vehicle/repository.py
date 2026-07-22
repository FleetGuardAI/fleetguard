"""
Vehicle Management Domain - Repository
"""

import abc
import uuid
from typing import List, Optional
from domain.vehicle.models import Vehicle

class BaseVehicleRepository(abc.ABC):
    @abc.abstractmethod
    def create(self, vehicle: Vehicle) -> None:
        pass
        
    @abc.abstractmethod
    def update(self, vehicle: Vehicle) -> None:
        pass
        
    @abc.abstractmethod
    def find_by_id(self, vehicle_id: uuid.UUID) -> Optional[Vehicle]:
        pass
        
    @abc.abstractmethod
    def find_by_registration(self, registration_number: str) -> Optional[Vehicle]:
        pass
        
    @abc.abstractmethod
    def find_by_vin(self, vin: str) -> Optional[Vehicle]:
        pass

    @abc.abstractmethod
    def find_by_chassis(self, chassis: str) -> Optional[Vehicle]:
        pass

    @abc.abstractmethod
    def find_by_engine(self, engine: str) -> Optional[Vehicle]:
        pass

    @abc.abstractmethod
    def find_by_organization(self, organization_id: uuid.UUID) -> List[Vehicle]:
        pass

    @abc.abstractmethod
    def search(self, **kwargs) -> List[Vehicle]:
        pass

    @abc.abstractmethod
    def exists(self, vehicle_id: uuid.UUID) -> bool:
        pass


class InMemoryVehicleRepository(BaseVehicleRepository):
    def __init__(self):
        self._vehicles = {}

    def create(self, vehicle: Vehicle) -> None:
        self._vehicles[vehicle.vehicle_id] = vehicle
        
    def update(self, vehicle: Vehicle) -> None:
        self._vehicles[vehicle.vehicle_id] = vehicle
        
    def find_by_id(self, vehicle_id: uuid.UUID) -> Optional[Vehicle]:
        return self._vehicles.get(vehicle_id)
        
    def find_by_registration(self, registration_number: str) -> Optional[Vehicle]:
        for v in self._vehicles.values():
            if v.registration_number.value == registration_number:
                return v
        return None
        
    def find_by_vin(self, vin: str) -> Optional[Vehicle]:
        for v in self._vehicles.values():
            if v.vin and v.vin.value == vin:
                return v
        return None

    def find_by_chassis(self, chassis: str) -> Optional[Vehicle]:
        for v in self._vehicles.values():
            if v.chassis_number and v.chassis_number.value == chassis:
                return v
        return None

    def find_by_engine(self, engine: str) -> Optional[Vehicle]:
        for v in self._vehicles.values():
            if v.engine_number and v.engine_number.value == engine:
                return v
        return None

    def find_by_organization(self, organization_id: uuid.UUID) -> List[Vehicle]:
        return [v for v in self._vehicles.values() if v.organization_id == organization_id]

    def search(self, **kwargs) -> List[Vehicle]:
        results = list(self._vehicles.values())
        if "status" in kwargs:
            results = [v for v in results if v.status == kwargs["status"]]
        if "category" in kwargs:
            results = [v for v in results if v.category == kwargs["category"]]
        if "fuel_type" in kwargs:
            results = [v for v in results if v.fuel_type == kwargs["fuel_type"]]
        return results

    def exists(self, vehicle_id: uuid.UUID) -> bool:
        return vehicle_id in self._vehicles
