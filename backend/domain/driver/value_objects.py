"""
Driver Management Domain - Value Objects
"""

import re
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator
from domain.driver.errors import InvalidIdentifier, InvalidLicence


class EmployeeCode(BaseModel):
    value: str

    model_config = ConfigDict(frozen=True)

    @field_validator("value")
    @classmethod
    def validate_format(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise InvalidIdentifier("Employee code cannot be empty.")
        if len(v) > 50:
            raise InvalidIdentifier("Employee code too long.")
        return v


class PhoneNumber(BaseModel):
    value: str

    model_config = ConfigDict(frozen=True)

    @field_validator("value")
    @classmethod
    def validate_format(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise InvalidIdentifier("Phone number cannot be empty.")
        # simplistic validation
        if not re.match(r"^\+?[0-9\-\s]{7,20}$", v):
            raise InvalidIdentifier(f"Invalid phone number format: {v}")
        return v


class EmailAddress(BaseModel):
    value: str

    model_config = ConfigDict(frozen=True)

    @field_validator("value")
    @classmethod
    def validate_format(cls, v: str) -> str:
        v = v.strip().lower()
        if not v:
            raise InvalidIdentifier("Email cannot be empty.")
        if "@" not in v:
            raise InvalidIdentifier(f"Invalid email format: {v}")
        return v


class LicenceClass(str, Enum):
    CLASS_A = "CLASS_A"
    CLASS_B = "CLASS_B"
    CLASS_C = "CLASS_C"
    CLASS_D = "CLASS_D"
    COMMERCIAL = "COMMERCIAL"


class DriverLicence(BaseModel):
    number: str
    licence_class: LicenceClass
    expiry_date: datetime
    state_of_issue: str

    model_config = ConfigDict(frozen=True)

    @field_validator("number")
    @classmethod
    def validate_number(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise InvalidLicence("Licence number cannot be empty.")
        return v

    def is_expired(self, current_time: datetime = None) -> bool:
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        return self.expiry_date < current_time
