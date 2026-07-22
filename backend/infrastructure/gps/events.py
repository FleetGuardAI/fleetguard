"""
GPS Gateway Framework - Operational Events
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class BaseGPSEvent(BaseModel):
    """
    Base immutable event representing a GPS observation.
    """
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    device_id: str
    provider: str
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class PositionRecorded(BaseGPSEvent):
    """
    Event emitted when a valid coordinate is received.
    """
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    heading: Optional[float] = None
    speed: Optional[float] = None
    accuracy: Optional[float] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IgnitionStateChanged(BaseGPSEvent):
    """
    Event emitted when an ignition change is detected or observed.
    Note: To be stateless, we might just emit 'IgnitionObserved',
    but per requirements we'll call it IgnitionStateChanged or similar.
    """
    ignition_on: bool
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
