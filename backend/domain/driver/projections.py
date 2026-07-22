"""
Driver Management Domain - Projections
"""

import uuid
from typing import Optional
from pydantic import BaseModel
from domain.driver.models import DriverStatus, EmploymentType
from domain.driver.value_objects import LicenceClass

class DriverSummary(BaseModel):
    """
    Flat read model projection.
    Notice we do not resolve actual `assigned_vehicle` ID here as that belongs to Assignment Domain.
    But a CQRS query service might stitch it later.
    """
    driver_id: uuid.UUID
    employee_code: str
    full_name: str
    licence_number: str
    licence_class: LicenceClass
    status: DriverStatus
    employment_type: EmploymentType
    is_licence_expired: bool
    
    @classmethod
    def from_domain(cls, driver) -> "DriverSummary":
        return cls(
            driver_id=driver.driver_id,
            employee_code=driver.employee_code.value,
            full_name=driver.full_name,
            licence_number=driver.licence.number,
            licence_class=driver.licence.licence_class,
            status=driver.status,
            employment_type=driver.employment_type,
            is_licence_expired=driver.licence.is_expired()
        )
