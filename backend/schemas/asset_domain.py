"""
FleetGuard — Asset Domain Pydantic Schemas
Defines value objects for asset operations and read-models for API responses.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, model_validator
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

    @model_validator(mode="after")
    def strip_secrets(self) -> "AssetResponse":
        if self.purchase_information and "api_key_hash" in self.purchase_information:
            # We don't want to mutate the DB object if it's attached, but Pydantic creates a copy for the model
            # However, since purchase_information is a dict, it might be by reference.
            # Let's create a new dict.
            self.purchase_information = {k: v for k, v in self.purchase_information.items() if k != "api_key_hash"}
        return self


# ===========================================================================
# Value Objects / Internal Commands / API Inputs
# ===========================================================================

class HardwareAssetCreate(BaseModel):
    api_key: str
    vehicle_id: int
    device_name: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "api_key": "sec_12345",
                "vehicle_id": 1,
                "device_name": "Truck 01 GPS"
            }
        }
    }

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
