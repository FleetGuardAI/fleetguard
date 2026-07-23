"""
Fuel Operations Domain - Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from domain.fuel.value_objects import Volume, Location

class TransactionType(str, Enum):
    FILL = "FILL"
    DRAIN = "DRAIN"
    BURN = "BURN"
    ADJUSTMENT = "ADJUSTMENT"

class FuelTransaction(BaseModel):
    """
    Immutable physical occurrence recorded on a vehicle's fuel ledger.
    """
    transaction_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    vehicle_id: str
    driver_assignment_id: Optional[uuid.UUID] = None
    trip_id: Optional[uuid.UUID] = None
    
    transaction_type: TransactionType
    volume: Volume
    
    location: Optional[Location] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = {"frozen": True, "extra": "forbid"}
