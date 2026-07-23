"""
Vehicle Management Domain - Events
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = {"frozen": True}


class VehicleRegistered(DomainEvent):
    vehicle_id: uuid.UUID
    registration_number: str
    organization_id: uuid.UUID
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VehicleActivated(DomainEvent):
    vehicle_id: uuid.UUID
    reason: Optional[str] = None


class VehicleDeactivated(DomainEvent):
    vehicle_id: uuid.UUID
    reason: Optional[str] = None


class VehicleArchived(DomainEvent):
    vehicle_id: uuid.UUID
    reason: Optional[str] = None


class VehicleRetired(DomainEvent):
    vehicle_id: uuid.UUID
    reason: Optional[str] = None


class VehicleUpdated(DomainEvent):
    vehicle_id: uuid.UUID
    reason: Optional[str] = None


class VehicleConfigurationChanged(DomainEvent):
    vehicle_id: uuid.UUID
    reason: Optional[str] = None


class VehicleSpecificationChanged(DomainEvent):
    vehicle_id: uuid.UUID
    reason: Optional[str] = None
