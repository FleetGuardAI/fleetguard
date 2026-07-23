"""
Fuel Operations Domain - Value Objects
"""

from pydantic import BaseModel, Field

class Volume(BaseModel):
    liters: float = 0.0
    model_config = {"frozen": True}

class TankCalibration(BaseModel):
    max_capacity_liters: float
    sensor_type: str = "DEFAULT"
    model_config = {"frozen": True}

class Location(BaseModel):
    latitude: float
    longitude: float
    address: str | None = None
    model_config = {"frozen": True}
