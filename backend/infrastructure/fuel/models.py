"""
Fuel Sensor Gateway Framework - Models
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class MeasurementUnit(str, Enum):
    LITRES = "LITRES"
    PERCENTAGE = "PERCENTAGE"
    MILLIMETERS = "MILLIMETERS"
    VOLTAGE = "VOLTAGE"
    ADC = "ADC"
    UNKNOWN = "UNKNOWN"


class TelemetryQuality(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class FuelProcessingStatus(str, Enum):
    SUCCESS = "SUCCESS"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NORMALIZATION_ERROR = "NORMALIZATION_ERROR"
    UNKNOWN_PROVIDER = "UNKNOWN_PROVIDER"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class FuelTelemetry(BaseModel):
    """
    Strict representation of a normalized fuel reading from a specific device.
    """
    telemetry_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    provider: str
    device_id: str
    timestamp: datetime
    fuel_level: float
    measurement_unit: MeasurementUnit
    quality: TelemetryQuality = TelemetryQuality.UNKNOWN
    temperature: Optional[float] = None
    sensor_health: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class FuelProcessingResult(BaseModel):
    """
    Wrapper for the output of fuel telemetry normalization.
    """
    telemetry: Optional[FuelTelemetry] = None
    operational_events: List[Any] = Field(default_factory=list)
    processing_status: FuelProcessingStatus
    execution_time_ms: float
    error_message: Optional[str] = None
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
