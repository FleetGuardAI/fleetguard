"""
FleetGuard — Driver Domain Pydantic Schemas
Defines value objects for driver operations and read-models for API responses.
"""

from typing import Optional
from pydantic import BaseModel, Field
from datetime import date
from models.driver_domain import DriverStatus, EmploymentStatus


# ===========================================================================
# Read Models
# ===========================================================================

class DriverResponse(BaseModel):
    id: int
    name: str
    phone_number: str
    avatar_url: Optional[str] = None
    
    # --- Identity & License ---
    employee_id: Optional[str] = None
    license_number: Optional[str] = None
    license_valid_until: Optional[date] = None

    # --- Business Status ---
    employment_status: Optional[EmploymentStatus] = None
    status: DriverStatus
    
    origin_type: Optional[str] = None
    origin_id: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


# ===========================================================================
# Value Objects / Internal Commands
# ===========================================================================

class DriverRegistered(BaseModel):
    name: str
    phone_number: str
    employee_id: Optional[str] = None
    employment_status: Optional[EmploymentStatus] = None


class DriverUpdated(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    avatar_url: Optional[str] = None
    employment_status: Optional[EmploymentStatus] = None


class DriverLicenseUpdated(BaseModel):
    license_number: str
    license_valid_until: Optional[date] = None


class DriverStatusChanged(BaseModel):
    status: DriverStatus
