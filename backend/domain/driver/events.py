"""
Driver Management Domain - Events
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = {"frozen": True}


class DriverRegistered(DomainEvent):
    driver_id: uuid.UUID
    employee_code: str
    organization_id: uuid.UUID
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DriverActivated(DomainEvent):
    driver_id: uuid.UUID
    reason: Optional[str] = None


class DriverDeactivated(DomainEvent):
    driver_id: uuid.UUID
    reason: Optional[str] = None
    

class DriverSuspended(DomainEvent):
    driver_id: uuid.UUID
    reason: Optional[str] = None


class DriverArchived(DomainEvent):
    driver_id: uuid.UUID
    reason: Optional[str] = None


class DriverRetired(DomainEvent):
    driver_id: uuid.UUID
    reason: Optional[str] = None


class DriverUpdated(DomainEvent):
    driver_id: uuid.UUID
    reason: Optional[str] = None


class DriverProfileUpdated(DomainEvent):
    driver_id: uuid.UUID


class DriverLicenceUpdated(DomainEvent):
    driver_id: uuid.UUID


class DriverPreferencesUpdated(DomainEvent):
    driver_id: uuid.UUID
