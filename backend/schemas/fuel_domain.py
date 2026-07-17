"""
FleetGuard — Fuel Domain Pydantic Schemas
Defines value objects for fuel operations and read-models for API responses.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from models.fuel_domain import FuelTransactionType


# ===========================================================================
# Value Objects / Internal Commands
# ===========================================================================

class FuelFill(BaseModel):
    """Internal value object representing a fuel fill action."""
    truck_id: int
    amount_liters: float = Field(..., gt=0)
    timestamp: datetime
    description: Optional[str] = None


class FuelAdjustment(BaseModel):
    """Internal value object representing a manual fuel adjustment."""
    truck_id: int
    amount_liters: float = Field(..., description="Can be positive or negative")
    timestamp: datetime
    description: Optional[str] = None


# ===========================================================================
# Response Schemas (Read Models)
# ===========================================================================

class FuelTransactionResponse(BaseModel):
    id: int
    truck_id: int
    transaction_type: FuelTransactionType
    amount_liters: float
    origin_type: Optional[str] = None
    origin_id: Optional[str] = None
    timestamp: datetime
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FuelStateResponse(BaseModel):
    id: int
    truck_id: int
    current_level: float
    origin_type: Optional[str] = None
    origin_id: Optional[str] = None
    last_updated_at: datetime

    model_config = {"from_attributes": True}


class FuelHistoryResponse(BaseModel):
    """Wraps a list of transactions to form the history."""
    truck_id: int
    history: list[FuelTransactionResponse]
