"""
Driver Management Domain - Service
"""

import uuid
from typing import List, Optional, Tuple
from domain.driver.models import Driver
from domain.driver.value_objects import EmployeeCode, PhoneNumber, EmailAddress
from domain.driver.aggregate import DriverAggregate
from domain.driver.repository import BaseDriverRepository
from domain.driver.schemas import RegisterDriverRequest
from domain.driver.errors import DuplicateDriver, DuplicateLicence, DriverNotFound
from domain.driver.events import DomainEvent

class DriverService:
    def __init__(self, repository: BaseDriverRepository):
        self.repository = repository
        
    def register_driver(self, request: RegisterDriverRequest) -> Tuple[Driver, List[DomainEvent]]:
        if self.repository.find_by_employee_code(request.employee_code):
            raise DuplicateDriver(f"Employee code {request.employee_code} is already in use.")
            
        if self.repository.find_by_licence(request.licence.number):
            raise DuplicateLicence(f"Licence number {request.licence.number} is already registered.")
            
        driver = Driver(
            organization_id=request.organization_id,
            employee_code=EmployeeCode(value=request.employee_code),
            full_name=request.full_name,
            phone_number=PhoneNumber(value=request.phone_number),
            email=EmailAddress(value=request.email) if request.email else None,
            licence=request.licence,
            employment_type=request.employment_type
        )
        
        registered_driver, events = DriverAggregate.register_driver(driver)
        self.repository.create(registered_driver)
        return registered_driver, events

    def activate_driver(self, driver_id: uuid.UUID, reason: Optional[str] = None) -> Tuple[Driver, List[DomainEvent]]:
        driver = self.repository.find_by_id(driver_id)
        if not driver:
            raise DriverNotFound(f"Driver {driver_id} not found.")
            
        updated, events = DriverAggregate.activate_driver(driver, reason)
        self.repository.update(updated)
        return updated, events
        
    def suspend_driver(self, driver_id: uuid.UUID, reason: Optional[str] = None) -> Tuple[Driver, List[DomainEvent]]:
        driver = self.repository.find_by_id(driver_id)
        if not driver:
            raise DriverNotFound(f"Driver {driver_id} not found.")
            
        updated, events = DriverAggregate.suspend_driver(driver, reason)
        self.repository.update(updated)
        return updated, events

    def get_driver(self, driver_id: uuid.UUID) -> Optional[Driver]:
        return self.repository.find_by_id(driver_id)
