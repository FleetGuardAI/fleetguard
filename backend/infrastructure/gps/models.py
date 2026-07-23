"""
GPS Gateway Framework - Models
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class GPSProcessingStatus(str, Enum):
    SUCCESS = "SUCCESS"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    NORMALIZATION_FAILED = "NORMALIZATION_FAILED"
    PROVIDER_NOT_FOUND = "PROVIDER_NOT_FOUND"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class ProviderCapabilities(BaseModel):
    """
    Explicitly models what telemetry a provider supports.
    """
    supports_ignition: bool = False
    supports_heading: bool = False
    supports_altitude: bool = False
    supports_speed: bool = True
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class GPSPosition(BaseModel):
    """
    Strict representation of a normalized GPS point from a specific device.
    Provider-centric, does not contain vehicle_id.
    """
    position_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    provider: str
    device_id: str
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None
    ignition: Optional[bool] = None
    timestamp: datetime
    accuracy: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class GPSProcessingResult(BaseModel):
    """
    Wrapper for the output of telemetry normalization.
    """
    position: Optional[GPSPosition] = None
    operational_events: List[Any] = Field(default_factory=list)
    processing_status: GPSProcessingStatus
    execution_time_ms: float
    error_message: Optional[str] = None
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
