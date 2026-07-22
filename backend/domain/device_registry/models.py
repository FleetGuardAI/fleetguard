"""
Device Registry & Mapping Framework - Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DeviceType(str, Enum):
    GPS_TRACKER = "GPS_TRACKER"
    FUEL_SENSOR = "FUEL_SENSOR"
    UNKNOWN = "UNKNOWN"


class DeviceStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"


class EntityType(str, Enum):
    VEHICLE = "VEHICLE"
    TRAILER = "TRAILER"
    DRIVER = "DRIVER"
    UNKNOWN = "UNKNOWN"


class MappingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Device(BaseModel):
    """
    Immutable representation of a registered hardware device.
    """
    device_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    provider: str
    serial_number: str
    device_type: DeviceType
    firmware_version: Optional[str] = None
    status: DeviceStatus = DeviceStatus.INACTIVE
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class DeviceMapping(BaseModel):
    """
    Immutable mapping linking a hardware device to a FleetGuard business entity.
    """
    mapping_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    device_id: uuid.UUID
    entity_type: EntityType
    entity_id: str
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    unassigned_at: Optional[datetime] = None
    status: MappingStatus = MappingStatus.ACTIVE
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
