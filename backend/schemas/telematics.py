"""
FleetGuard — Telematics API Schemas
Normalized schemas for hardware telematics processing.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class NormalizedHardwareEvent(BaseModel):
    """
    Internal normalized event representing a single location point 
    from a hardware GPS provider.
    """
    device_imei: Optional[str] = Field(
        None, description="The unique device identifier / IMEI / serial number"
    )
    vehicle_registration: Optional[str] = Field(
        None, description="Optional vehicle registration plate. Used for testing/fallback if allowed by config."
    )
    
    latitude: float
    longitude: float
    timestamp: datetime
    
    speed: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None
    ignition_status: Optional[bool] = None
    
    # Provider-specific fields can be stuffed into source_metadata
    source_metadata: Dict[str, Any] = Field(default_factory=dict)
    
class TelematicsBatchResponseItem(BaseModel):
    timestamp: datetime
    status: str
    reason: Optional[str] = None

class TelematicsBatchResponse(BaseModel):
    accepted: int
    duplicates: int
    rejected: int
    items: list[TelematicsBatchResponseItem]
