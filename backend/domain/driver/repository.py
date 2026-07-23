"""
Driver Management Domain - Repository
"""

import abc
import uuid
from typing import List, Optional
from domain.driver.models import Driver

class BaseDriverRepository(abc.ABC):
    @abc.abstractmethod
    def create(self, driver: Driver) -> None:
        pass
        
    @abc.abstractmethod
    def update(self, driver: Driver) -> None:
        pass
        
    @abc.abstractmethod
    def find_by_id(self, driver_id: uuid.UUID) -> Optional[Driver]:
        pass
        
    @abc.abstractmethod
    def find_by_employee_code(self, employee_code: str) -> Optional[Driver]:
        pass
        
    @abc.abstractmethod
    def find_by_licence(self, licence_number: str) -> Optional[Driver]:
        pass

    @abc.abstractmethod
    def find_by_phone(self, phone: str) -> Optional[Driver]:
        pass

    @abc.abstractmethod
    def find_by_email(self, email: str) -> Optional[Driver]:
        pass

    @abc.abstractmethod
    def find_by_organization(self, organization_id: uuid.UUID) -> List[Driver]:
        pass

    @abc.abstractmethod
    def search(self, **kwargs) -> List[Driver]:
        pass

    @abc.abstractmethod
    def exists(self, driver_id: uuid.UUID) -> bool:
        pass


class InMemoryDriverRepository(BaseDriverRepository):
    def __init__(self):
        self._drivers = {}

    def create(self, driver: Driver) -> None:
        self._drivers[driver.driver_id] = driver
        
    def update(self, driver: Driver) -> None:
        self._drivers[driver.driver_id] = driver
        
    def find_by_id(self, driver_id: uuid.UUID) -> Optional[Driver]:
        return self._drivers.get(driver_id)
        
    def find_by_employee_code(self, employee_code: str) -> Optional[Driver]:
        for d in self._drivers.values():
            if d.employee_code.value == employee_code:
                return d
        return None
        
    def find_by_licence(self, licence_number: str) -> Optional[Driver]:
        for d in self._drivers.values():
            if d.licence.number == licence_number:
                return d
        return None

    def find_by_phone(self, phone: str) -> Optional[Driver]:
        for d in self._drivers.values():
            if d.phone_number.value == phone:
                return d
        return None

    def find_by_email(self, email: str) -> Optional[Driver]:
        for d in self._drivers.values():
            if d.email and d.email.value == email:
                return d
        return None

    def find_by_organization(self, organization_id: uuid.UUID) -> List[Driver]:
        return [d for d in self._drivers.values() if d.organization_id == organization_id]

    def search(self, **kwargs) -> List[Driver]:
        results = list(self._drivers.values())
        if "status" in kwargs:
            results = [d for d in results if d.status == kwargs["status"]]
        if "employment_type" in kwargs:
            results = [d for d in results if d.employment_type == kwargs["employment_type"]]
        return results

    def exists(self, driver_id: uuid.UUID) -> bool:
        return driver_id in self._drivers
