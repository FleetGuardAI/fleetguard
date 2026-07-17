"""
FleetGuard — Tyre Domain Pydantic Schemas
Defines value objects for tyre operations and read-models for API responses.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel
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
    event_category: LifecycleEventCategory
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None
    
    origin_type: Optional[str] = None
    origin_id: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class TyreResponse(BaseModel):
    id: int
    serial_number: str
    current_status: TyreStatus
    
    manufacturer: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    size: Optional[str] = None
    
    purchase_information: Optional[Dict[str, Any]] = None

    current_vehicle_id: Optional[int] = None
    current_position: Optional[str] = None

    lifecycle_records: List[TyreLifecycleRecordResponse] = []

    origin_type: Optional[str] = None
    origin_id: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


# ===========================================================================
# Value Objects / Internal Commands
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
