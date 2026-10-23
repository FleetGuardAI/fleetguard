"""
FleetGuard — Fuel Domain Pydantic Schemas
Defines value objects for fuel operations and read-models for API responses.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from models.fuel_domain import FuelTransactionType, FuelSource, FuelStateReliability


# ===========================================================================
# Value Objects / Internal Commands
# ===========================================================================

class FuelFill(BaseModel):
    """Internal value object representing a fuel fill action."""
    vehicle_id: int
    amount_liters: float = Field(..., gt=0)
    timestamp: datetime
    description: Optional[str] = None


class FuelAdjustment(BaseModel):
    """Internal value object representing a manual fuel adjustment."""
    vehicle_id: int
    amount_liters: float = Field(..., description="Can be positive or negative")
    timestamp: datetime
    description: Optional[str] = None


# ===========================================================================
# Response Schemas (Read Models)
# ===========================================================================

class FuelTransactionCreate(BaseModel):
    vehicle_id: int
    driver_id: Optional[int] = None
    trip_id: Optional[int] = None
    fuel_type: Optional[str] = "DIESEL"
    quantity_liters: float = Field(..., gt=0)
    price_per_liter: float = Field(..., ge=0)
    odometer: Optional[float] = Field(None, ge=0)
    station: Optional[str] = None
    receipt_url: Optional[str] = None
    occurred_at: Optional[datetime] = None
    description: Optional[str] = None

class FuelTransactionResponse(BaseModel):
    id: int
    company_id: int
    vehicle_id: int
    driver_id: Optional[int] = None
    trip_id: Optional[int] = None
    expense_id: Optional[int] = None
    transaction_type: FuelTransactionType
    amount_liters: float
    fuel_type: Optional[str] = None
    price_per_liter: Optional[float] = None
    total_cost: Optional[float] = None
    odometer: Optional[float] = None
    station: Optional[str] = None
    receipt_url: Optional[str] = None
    
    # Reconciliation
    reconciliation_status: Optional[str] = None
    reconciled_sensor_liters: Optional[float] = None
    variance_liters: Optional[float] = None
    
    origin_type: Optional[str] = None
    origin_id: Optional[str] = None
    timestamp: datetime
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FuelStateResponse(BaseModel):
    id: int
    vehicle_id: int
    current_level: float
    source: FuelSource
    reliability: FuelStateReliability
    last_operational_event_id: Optional[str] = None
    last_updated_at: datetime

    model_config = {"from_attributes": True}


class CurrentFuelState(BaseModel):
    """
    Domain object used by Validation Engine and business logic.
    Provides a complete view of the current fuel state without requiring DB queries.
    """
    vehicle_id: int
    current_fuel_liters: float
    capacity_liters: float
    source: FuelSource
    reliability: FuelStateReliability
    last_updated: datetime
    last_operational_event_id: Optional[str] = None


class FuelHistoryResponse(BaseModel):
    """Wraps a list of transactions to form the history."""
    vehicle_id: int
    history: list[FuelTransactionResponse]
