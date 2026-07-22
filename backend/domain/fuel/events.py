"""
Fuel Operations Domain - Events
"""

import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class DomainEvent(BaseModel):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_config = {"frozen": True}

class FuelFillRecorded(DomainEvent):
    vehicle_id: str
    transaction_id: uuid.UUID
    volume_liters: float
    new_balance_liters: float
    driver_assignment_id: uuid.UUID | None = None
    trip_id: uuid.UUID | None = None

class FuelDrainRecorded(DomainEvent):
    vehicle_id: str
    transaction_id: uuid.UUID
    volume_liters: float
    new_balance_liters: float
    driver_assignment_id: uuid.UUID | None = None
    trip_id: uuid.UUID | None = None

class FuelBalanceUpdated(DomainEvent):
    vehicle_id: str
    new_balance_liters: float

class FuelCalibrationUpdated(DomainEvent):
    vehicle_id: str
    max_capacity_liters: float
