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
    age: Optional[int] = None
    avatar_url: Optional[str] = None
    
    # --- Identity & License ---
    employee_id: Optional[str] = None
    license_number: Optional[str] = None
    license_valid_until: Optional[date] = None

    # --- Document URLs ---
    license_front_url: Optional[str] = None
    license_back_url: Optional[str] = None
    aadhaar_front_url: Optional[str] = None
    aadhaar_back_url: Optional[str] = None
    selfie_url: Optional[str] = None

    # --- Onboarding & Verification ---
    verification_status: Optional[str] = None
    face_verified: Optional[bool] = None

    # --- Business Status ---
    employment_status: Optional[EmploymentStatus] = None
    status: DriverStatus
    
    # --- Assignment ---
    assigned_vehicle: Optional[str] = None
    
    origin_type: Optional[str] = None
    origin_id: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


# ===========================================================================
# Write Models / Commands
# ===========================================================================

class DriverCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Driver's full name")
    phone_number: str = Field(..., min_length=5, description="Driver's mobile number")
    avatar_url: Optional[str] = Field(None, description="Optional avatar URL")
    employee_id: Optional[str] = None
    license_number: Optional[str] = None
    employment_status: Optional[EmploymentStatus] = None


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
