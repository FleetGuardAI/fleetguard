"""
FleetGuard — Asset Domain Pydantic Schemas
Defines value objects for asset operations and read-models for API responses.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel
from datetime import datetime

from models.asset_domain import (
    AssetType,
    AssetInstallationStatus,
    AssetOperationalStatus,
    AssetHistoryCategory
)


# ===========================================================================
# Read Models
# ===========================================================================

class AssetHistoryResponse(BaseModel):
    id: int
    event_category: AssetHistoryCategory
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None
    
    origin_type: Optional[str] = None
    origin_id: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class AssetResponse(BaseModel):
    id: int
    business_id: str
    asset_type: AssetType
    
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    
    purchase_information: Optional[Dict[str, Any]] = None
    warranty_information: Optional[Dict[str, Any]] = None

    current_vehicle_id: Optional[int] = None
    installation_status: AssetInstallationStatus
    operational_status: AssetOperationalStatus

    history_records: List[AssetHistoryResponse] = []

    origin_type: Optional[str] = None
    origin_id: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


# ===========================================================================
# Value Objects / Internal Commands
# ===========================================================================

class AssetRegistered(BaseModel):
    asset_type: str
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    purchase_information: Optional[Dict[str, Any]] = None
    warranty_information: Optional[Dict[str, Any]] = None


class AssetInstalled(BaseModel):
    vehicle_id: int
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None


class AssetRemoved(BaseModel):
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None


class AssetCalibrated(BaseModel):
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None


class AssetRepaired(BaseModel):
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None


class AssetReplaced(BaseModel):
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None


class AssetRetired(BaseModel):
    performed_at: datetime
    details: Optional[Dict[str, Any]] = None
