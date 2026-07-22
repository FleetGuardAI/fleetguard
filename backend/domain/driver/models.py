"""
Driver Management Domain - Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from domain.driver.value_objects import EmployeeCode, PhoneNumber, EmailAddress, DriverLicence


class DriverStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"
    ARCHIVED = "ARCHIVED"


class EmploymentType(str, Enum):
    FULL_TIME = "FULL_TIME"
    CONTRACT = "CONTRACT"
    PART_TIME = "PART_TIME"
    TEMPORARY = "TEMPORARY"


class DriverProfile(BaseModel):
    emergency_contact: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None
    preferred_language: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}


class DriverPreferences(BaseModel):
    notification_preferences: Dict[str, Any] = Field(default_factory=dict)
    communication_preferences: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}


class Driver(BaseModel):
    """
    Immutable representation of a Driver entity.
    Mutable state transitions should be done via creating a new copy.
    """
    driver_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    organization_id: uuid.UUID
    employee_code: EmployeeCode
    full_name: str
    phone_number: PhoneNumber
    email: Optional[EmailAddress] = None
    
    licence: DriverLicence
    
    status: DriverStatus = DriverStatus.INACTIVE
    employment_type: EmploymentType
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    profile: DriverProfile = Field(default_factory=DriverProfile)
    preferences: DriverPreferences = Field(default_factory=DriverPreferences)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}
