"""
FleetGuard — Tyre Domain Pydantic Schemas
Defines value objects for tyre operations and read-models for API responses.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

from models.tyre_domain import (
    TyreStatus,
    LifecycleEventCategory
)


# ===========================================================================
# Read Models
# ===========================================================================

class TyreLifecycleRecordResponse(BaseModel):
    id: int
    company_id: Optional[int] = None
    event_category: LifecycleEventCategory
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None
    
    origin_type: Optional[str] = None
    origin_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TyreResponse(BaseModel):
    id: int
    company_id: Optional[int] = None
    serial_number: str
    current_status: TyreStatus
    
    manufacturer: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    size: Optional[str] = None
    
    purchase_cost: Optional[float] = None
    purchase_date: Optional[datetime] = None
    purchase_currency: str = "INR"
    purchase_invoice: Optional[str] = None
    purchase_vendor: Optional[str] = None
    purchase_information: Optional[Dict[str, Any]] = None

    current_vehicle_id: Optional[int] = None
    current_position: Optional[str] = None

    retread_count: int = 0
    total_lifetime_km: float = 0.0
    current_retread_km: float = 0.0
    current_installation_odometer: Optional[float] = None
    current_tread_depth_mm: Optional[float] = None

    lifecycle_records: List[TyreLifecycleRecordResponse] = []

    origin_type: Optional[str] = None
    origin_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TyreInventorySummaryResponse(BaseModel):
    total_tyres: int
    in_storage: int
    installed: int
    retreading: int
    in_repair: int
    retired: int


class StateValuationSummary(BaseModel):
    state: TyreStatus
    total_count: int
    known_cost_count: int
    unknown_cost_count: int
    total_acquisition_value: float
    coverage_pct: float

    model_config = ConfigDict(from_attributes=True)


class TyreInventoryValuationResponse(BaseModel):
    as_of: datetime
    currency: str = "INR"
    valuation_method: str = "KNOWN_ACQUISITION_COST"

    # Active operational fleet assets (IN_STORAGE, INSTALLED, RETREADING, IN_REPAIR)
    total_active_tyres: int
    total_active_acquisition_value: float
    active_known_cost_count: int
    active_unknown_cost_count: int
    active_coverage_pct: float

    # Total owned including RETIRED
    total_owned_tyres: int
    total_owned_acquisition_value: float
    total_known_cost_count: int
    total_unknown_cost_count: int
    total_coverage_pct: float

    # Partitioned by lifecycle state
    by_lifecycle_state: Dict[str, StateValuationSummary]

    # Separately tracked recognized service expenses (from Expense ledger)
    total_retread_expenditure: float
    total_repair_expenditure: float

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# Request Models
# ===========================================================================

class TyreCreateRequest(BaseModel):
    serial_number: str
    manufacturer: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    size: Optional[str] = None
    initial_tread_mm: Optional[float] = Field(None, ge=0.0)
    purchase_cost: Optional[float] = Field(None, ge=0.0)
    purchase_date: Optional[str] = None
    purchase_currency: Optional[str] = "INR"
    invoice_number: Optional[str] = None
    vendor: Optional[str] = None
    record_purchase_expense: bool = False
    details: Optional[Dict[str, Any]] = None


class TyreInstallRequest(BaseModel):
    vehicle_id: int
    position: str
    odometer_km: Optional[float] = None
    performed_at: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None


class TyreRemoveRequest(BaseModel):
    odometer_km: Optional[float] = None
    target_status: Optional[str] = "IN_STORAGE"  # IN_STORAGE, RETREADING, IN_REPAIR, RETIRED
    reason: Optional[str] = None
    performed_at: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None


class TyreRotateRequest(BaseModel):
    new_position: str
    swap_serial_number: Optional[str] = None
    odometer_km: Optional[float] = None
    performed_at: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None


class TyreRetreadRequest(BaseModel):
    action: str = "COMPLETED"  # COMPLETED or REJECTED
    vendor: Optional[str] = None
    cost: Optional[float] = None
    tread_depth_mm: Optional[float] = None
    rejection_reason: Optional[str] = None
    receipt_reference: Optional[str] = None
    performed_at: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None


class TyreRepairRequest(BaseModel):
    repair_type: str = "PUNCTURE"
    cost: Optional[float] = None
    workshop: Optional[str] = None
    receipt_reference: Optional[str] = None
    return_to_storage: bool = True
    performed_at: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None


class TyreRetireRequest(BaseModel):
    reason: str
    salvage_value: Optional[float] = None
    performed_at: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None


# ===========================================================================
# Value Objects / Internal Commands (Legacy compatibility)
# ===========================================================================

class TyreRegistered(BaseModel):
    manufacturer: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    size: Optional[str] = None
    purchase_information: Optional[Dict[str, Any]] = None


class TyreInstalled(BaseModel):
    vehicle_id: int
    position: str
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None


class TyreRemoved(BaseModel):
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None


class TyreRotated(BaseModel):
    new_position: str
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None


class TyreRepaired(BaseModel):
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None


class TyreRetreaded(BaseModel):
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None


class TyreRetired(BaseModel):
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None

