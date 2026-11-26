"""
FleetGuard / Vahan — Asset & Hardware Domain Pydantic Schemas
Defines schemas for universal hardware device registration, telematics status,
GPS provider management, location history, and dashboard summaries.
"""

from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone

from models.asset_domain import (
    AssetType,
    AssetInstallationStatus,
    AssetOperationalStatus,
    AssetHistoryCategory,
    ConnectionStatus,
    ConnectionType
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
            self.purchase_information = {k: v for k, v in self.purchase_information.items() if k != "api_key_hash"}
        return self


class HardwareDashboardSummary(BaseModel):
    total_devices: int = Field(0, description="Total registered GPS/telematics devices")
    connected_devices: int = Field(0, description="Devices communicating within threshold")
    disconnected_devices: int = Field(0, description="Devices that have missed communication threshold")
    pending_devices: int = Field(0, description="Devices registered but awaiting first telemetry signal")
    vehicles_with_gps: int = Field(0, description="Fleet vehicles with an active GPS device assigned")
    vehicles_without_gps: int = Field(0, description="Fleet vehicles without any active GPS device")


class HardwareDeviceResponse(BaseModel):
    id: int
    company_id: int
    business_id: str
    device_name: Optional[str] = None
    asset_type: AssetType = AssetType.GPS_DEVICE
    
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    imei: Optional[str] = None
    serial_number: Optional[str] = None
    firmware_version: Optional[str] = None
    
    connection_type: str = ConnectionType.DIRECT_HARDWARE.value
    connection_status: str = ConnectionStatus.PENDING.value
    protocol: Optional[str] = None
    gps_provider: Optional[str] = None
    
    current_vehicle_id: Optional[int] = None
    vehicle_registration: Optional[str] = None
    vehicle_name: Optional[str] = None
    
    installation_status: AssetInstallationStatus = AssetInstallationStatus.REGISTERED
    operational_status: AssetOperationalStatus = AssetOperationalStatus.OK
    
    last_communication_at: Optional[datetime] = None
    last_known_lat: Optional[float] = None
    last_known_lng: Optional[float] = None
    last_known_speed: Optional[float] = None
    last_known_heading: Optional[float] = None
    last_known_ignition: Optional[bool] = None
    last_known_battery: Optional[float] = None
    last_known_address: Optional[str] = None
    
    installation_date: Optional[datetime] = None
    offline_threshold_minutes: int = 15
    is_stale: bool = False
    
    connection_config: Optional[Dict[str, Any]] = None
    history_records: List[AssetHistoryResponse] = []
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


class HardwareDeviceListResponse(BaseModel):
    total: int
    items: List[HardwareDeviceResponse]
    page: int
    page_size: int
    total_pages: int


class GPSProviderAccountResponse(BaseModel):
    id: int
    company_id: int
    provider_type: str
    name: str
    server_url: Optional[str] = None
    account_id: Optional[str] = None
    sync_status: str
    last_sync_at: Optional[datetime] = None
    sync_error: Optional[str] = None
    device_count: int = 0
    config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class DeviceLocationPoint(BaseModel):
    id: int
    latitude: float
    longitude: float
    speed: Optional[float] = None
    speed_kmh: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None
    timestamp: datetime
    ignition: Optional[bool] = None


class DeviceLocationHistoryResponse(BaseModel):
    device_id: int
    device_name: Optional[str] = None
    imei: Optional[str] = None
    vehicle_id: Optional[int] = None
    vehicle_registration: Optional[str] = None
    total_points: int
    distance_km: float
    max_speed_kmh: float
    avg_speed_kmh: float
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    points: List[DeviceLocationPoint] = []


class DeviceTestConnectionResponse(BaseModel):
    success: bool
    status: str
    message: str
    last_communication: Optional[datetime] = None
    details: Dict[str, Any] = {}


# ===========================================================================
# Input Commands & Payloads
# ===========================================================================

class HardwareDeviceRegisterRequest(BaseModel):
    device_name: str = Field(..., min_length=2, max_length=100)
    connection_type: str = Field(..., description="GPS_PROVIDER_API, DIRECT_HARDWARE, TCP_DEVICE, MQTT_DEVICE, WEBHOOK, OTHER")
    manufacturer: str = Field(..., min_length=2, max_length=100)
    model: Optional[str] = None
    protocol: Optional[str] = None
    imei: str = Field(..., min_length=4, max_length=100, description="Device unique identifier / IMEI")
    serial_number: Optional[str] = None
    
    vehicle_id: Optional[int] = Field(None, description="Optional vehicle ID to assign immediately")
    gps_provider: Optional[str] = None
    
    # Sensitive credentials (encrypted server-side, never returned in responses)
    credentials: Optional[Dict[str, Any]] = Field(default_factory=dict, description="api_key, access_token, device_password, mqtt_password, webhook_secret")
    
    # Non-sensitive connection parameters (server host, port, topic, endpoint)
    connection_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    offline_threshold_minutes: int = Field(15, ge=1, le=1440)


class HardwareDeviceUpdateRequest(BaseModel):
    device_name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    protocol: Optional[str] = None
    gps_provider: Optional[str] = None
    offline_threshold_minutes: Optional[int] = None
    connection_config: Optional[Dict[str, Any]] = None
    credentials: Optional[Dict[str, Any]] = None


class VehicleReassignRequest(BaseModel):
    vehicle_id: Optional[int] = Field(None, description="Target vehicle ID or null to unassign/store")
    force: bool = Field(False, description="Whether to unassign any existing device on target vehicle")


class GPSProviderAccountCreateRequest(BaseModel):
    provider_type: str = Field(..., description="traccar, teltonika, queclink, generic_webhook, custom")
    name: str = Field(..., min_length=2, max_length=100)
    server_url: Optional[str] = None
    account_id: Optional[str] = None
    credentials: Optional[str] = Field(None, description="Admin token, API key, or user:password string")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PreRegistrationTestRequest(BaseModel):
    connection_type: str
    provider_type: Optional[str] = None
    server_url: Optional[str] = None
    credentials: Optional[str] = None
    protocol: Optional[str] = None
    imei: Optional[str] = None


# Legacy compatibility schema
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


# ===========================================================================
# Super-Admin Quarantine Governance Schemas
# ===========================================================================

class QuarantinedAssetItem(BaseModel):
    id: int
    business_id: str
    device_name: str
    imei: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    protocol: Optional[str] = None
    connection_status: str
    last_communication_at: Optional[datetime] = None
    created_at: datetime
    quarantine_company_id: int

    model_config = {"from_attributes": True}


class QuarantinedAssetReassignRequest(BaseModel):
    target_company_id: int
    target_vehicle_id: Optional[int] = None
    reason: str = Field(..., min_length=3, description="Audit justification for reassigning quarantined hardware")

