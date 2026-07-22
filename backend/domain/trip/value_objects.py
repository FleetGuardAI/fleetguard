"""
Trip Management Domain - Value Objects
"""

import uuid
from pydantic import BaseModel, Field

class TripId(BaseModel):
    value: uuid.UUID = Field(default_factory=uuid.uuid4)
    model_config = {"frozen": True}

class Location(BaseModel):
    latitude: float
    longitude: float
    address: str | None = None
    model_config = {"frozen": True}

class Distance(BaseModel):
    value_km: float = 0.0
    model_config = {"frozen": True}

class Duration(BaseModel):
    value_seconds: int = 0
    model_config = {"frozen": True}
