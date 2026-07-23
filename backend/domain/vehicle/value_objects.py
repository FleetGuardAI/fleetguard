"""
Vehicle Management Domain - Value Objects
"""

import re
from pydantic import BaseModel, ConfigDict, Field, field_validator
from domain.vehicle.errors import InvalidIdentifier

class RegistrationNumber(BaseModel):
    value: str

    model_config = ConfigDict(frozen=True)

    @field_validator("value")
    @classmethod
    def validate_format(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise InvalidIdentifier("Registration number cannot be empty.")
        # Simplistic validation: Alphanumeric and hyphens only, 2-15 chars
        if not re.match(r"^[A-Z0-9\-]{2,15}$", v):
            raise InvalidIdentifier(f"Invalid registration number format: {v}")
        return v


class VIN(BaseModel):
    value: str

    model_config = ConfigDict(frozen=True)

    @field_validator("value")
    @classmethod
    def validate_format(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise InvalidIdentifier("VIN cannot be empty.")
        # Standard VIN is 17 characters, excluding I, O, Q
        if not re.match(r"^[A-HJ-NPR-Z0-9]{17}$", v):
            raise InvalidIdentifier(f"Invalid VIN format: {v}")
        return v


class EngineNumber(BaseModel):
    value: str

    model_config = ConfigDict(frozen=True)

    @field_validator("value")
    @classmethod
    def validate_format(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise InvalidIdentifier("Engine number cannot be empty.")
        if len(v) < 3 or len(v) > 30:
            raise InvalidIdentifier("Engine number must be between 3 and 30 characters.")
        return v


class ChassisNumber(BaseModel):
    value: str

    model_config = ConfigDict(frozen=True)

    @field_validator("value")
    @classmethod
    def validate_format(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise InvalidIdentifier("Chassis number cannot be empty.")
        if len(v) < 3 or len(v) > 30:
            raise InvalidIdentifier("Chassis number must be between 3 and 30 characters.")
        return v
