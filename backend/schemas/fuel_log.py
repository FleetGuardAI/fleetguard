"""
FleetGuard — FuelLog Pydantic Schemas
Request/response models for the Fuel Monitoring API.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class FuelLogCreate(BaseModel):
    """Schema for ingesting a fuel reading (from IoT listener)."""
    truck_id: int
    timestamp: datetime
    raw_level: float = Field(
        ..., ge=0,
        examples=[245.3],
        description="Raw fuel sensor reading in liters"
    )
    expected_level: float = Field(
        0.0, ge=0,
        description="Expected fuel level based on consumption model"
    )
    speed: float = Field(
        0.0, ge=0,
        examples=[62.5],
        description="Vehicle speed in km/h"
    )
    latitude: float = Field(0.0, ge=-90, le=90)
    longitude: float = Field(0.0, ge=-180, le=180)


class FuelLogResponse(BaseModel):
    """Schema for fuel log API responses."""
    id: int
    truck_id: int
    timestamp: datetime
    raw_level: float
    filtered_level: float
    expected_level: float
    speed: float
    latitude: float
    longitude: float
    is_theft_alert: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FuelAlertResponse(BaseModel):
    """Schema for fuel theft alert details."""
    id: int
    truck_id: int
    truck_plate: Optional[str] = None
    timestamp: datetime
    fuel_drop_liters: float = Field(description="Amount of fuel drop in liters")
    filtered_level_before: float
    filtered_level_after: float
    speed: float
    latitude: float
    longitude: float
    created_at: datetime


class FuelChartData(BaseModel):
    """Time-series data point for the fuel monitoring chart."""
    timestamp: datetime
    expected_level: float = Field(description="Expected burn curve")
    actual_filtered_level: float = Field(description="EMA-smoothed actual level")
    raw_level: float = Field(description="Raw noisy sensor value")
    is_theft_alert: bool = False
