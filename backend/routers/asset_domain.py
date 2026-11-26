"""
FleetGuard / Vahan — Asset & Hardware Telematics Domain API Router
Provides comprehensive, production-ready REST APIs for the Hardware Assets module,
Universal Multi-Protocol GPS Integrations, Device-to-Vehicle Lifecycle,
Real-Time Telematics Diagnostics, and Provider Synchronization.

Security: All endpoints require authentication and enforce strict company-level tenant isolation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
import uuid

from database import get_db
from models.asset_domain import (
    Asset,
    AssetType,
    AssetInstallationStatus,
    AssetOperationalStatus,
    ConnectionStatus,
    ConnectionType,
)
from models.vehicle_domain import Vehicle
from models.user import User
from models.admin_domain import AdminUser
from schemas.asset_domain import (
    AssetResponse,
    HardwareAssetCreate,
    HardwareDashboardSummary,
    HardwareDeviceResponse,
    HardwareDeviceListResponse,
    HardwareDeviceRegisterRequest,
    HardwareDeviceUpdateRequest,
    VehicleReassignRequest,
    DeviceTestConnectionResponse,
    DeviceLocationHistoryResponse,
    GPSProviderAccountCreateRequest,
    GPSProviderAccountResponse,
    PreRegistrationTestRequest,
    QuarantinedAssetItem,
    QuarantinedAssetReassignRequest,
)
from services.auth_service import get_current_user
from services.admin_auth_service import require_admin_permission
from services.hardware_service import HardwareService
from domain.hardware_registry.verified_protocols import get_verified_registry

router = APIRouter(prefix="/v1", tags=["Hardware & Asset Domain"])


# ===========================================================================
# 1. Hardware Dashboard Summary & Protocols Registry
# ===========================================================================

@router.get("/assets/hardware/stats", response_model=HardwareDashboardSummary)
async def get_hardware_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HardwareDashboardSummary:
    """
    Returns real backend figures for all dashboard summary cards:
    - Total Hardware Devices
    - Connected Devices
    - Disconnected Devices
    - Devices Pending Configuration
    - Vehicles With GPS
    - Vehicles Without GPS
    """
    return await HardwareService.get_dashboard_summary(current_user.company_id, db)


@router.get("/assets/hardware/protocols")
async def get_protocols_compatibility_registry(
    current_user: User = Depends(get_current_user),
):
    """
    Returns verified protocol specifications, hardware manufacturers, models,
    default ports, and connection types.
    """
    return get_verified_registry()


@router.post("/assets/hardware/test-connection", response_model=DeviceTestConnectionResponse)
async def test_pre_registration_connection(
    payload: PreRegistrationTestRequest,
    current_user: User = Depends(get_current_user),
) -> DeviceTestConnectionResponse:
    """
    Pre-registration connectivity verification: validates provider credentials
    or hardware protocol configuration before saving.
    """
    return await HardwareService.test_pre_registration(payload)


# ===========================================================================
# 2. Hardware Devices List, Search & Details
# ===========================================================================

@router.get("/assets/hardware/devices", response_model=HardwareDeviceListResponse)
async def list_hardware_devices(
    search: Optional[str] = Query(None, description="Search vehicle, IMEI, or device name"),
    manufacturer: Optional[str] = Query("all", description="Filter by manufacturer"),
    connection_status: Optional[str] = Query("all", description="Filter by status: connected, disconnected, pending, error, maintenance"),
    gps_provider: Optional[str] = Query("all", description="Filter by GPS provider"),
    vehicle_assignment: Optional[str] = Query("all", description="all, assigned, unassigned"),
    sort_by: str = Query("created_at", description="device_name, imei, manufacturer, last_communication_at, installation_date, created_at"),
    sort_desc: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HardwareDeviceListResponse:
    """
    Retrieves filtered, searchable, sorted, and paginated hardware assets.
    Company-scoped tenant isolation.
    """
    return await HardwareService.list_devices(
        company_id=current_user.company_id,
        db=db,
        search=search,
        manufacturer=manufacturer,
        connection_status=connection_status,
        gps_provider=gps_provider,
        vehicle_assignment=vehicle_assignment,
        sort_by=sort_by,
        sort_desc=sort_desc,
        page=page,
        page_size=page_size,
    )


@router.get("/assets/hardware/devices/{asset_id}", response_model=HardwareDeviceResponse)
async def get_hardware_device_details(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HardwareDeviceResponse:
    """
    Fetches full device details including live telemetry cache, assigned vehicle,
    and operational history log.
    """
    return await HardwareService.get_device_by_id(current_user.company_id, asset_id, db)


# ===========================================================================
# 3. Device Lifecycle Actions (Register, Edit, Reassign, Test, Disconnect, Retire)
# ===========================================================================

@router.post("/assets/hardware/register", response_model=HardwareDeviceResponse, status_code=status.HTTP_201_CREATED)
async def register_hardware_device(
    payload: HardwareDeviceRegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HardwareDeviceResponse:
    """
    Registers a new hardware device through the multi-step registration workflow.
    Validates IMEI, checks conflicts, encrypts credentials, and establishes tenant ownership.
    """
    return await HardwareService.register_device(current_user.company_id, payload, db)


@router.put("/assets/hardware/devices/{asset_id}", response_model=HardwareDeviceResponse)
async def update_hardware_device(
    asset_id: int,
    payload: HardwareDeviceUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HardwareDeviceResponse:
    """Updates device metadata, protocol, or connection settings."""
    return await HardwareService.update_device(current_user.company_id, asset_id, payload, db)


@router.post("/assets/hardware/devices/{asset_id}/reassign", response_model=HardwareDeviceResponse)
async def reassign_vehicle(
    asset_id: int,
    payload: VehicleReassignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HardwareDeviceResponse:
    """
    Reassigns device to a vehicle or moves it to storage.
    Preserves historical GPS records without corrupting tracking data.
    """
    return await HardwareService.reassign_vehicle(current_user.company_id, asset_id, payload, db)


@router.post("/assets/hardware/devices/{asset_id}/disconnect", response_model=HardwareDeviceResponse)
async def disconnect_hardware_device(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HardwareDeviceResponse:
    """Disconnects device and moves it to unassigned storage."""
    return await HardwareService.disconnect_device(current_user.company_id, asset_id, db)


@router.delete("/assets/hardware/devices/{asset_id}")
async def remove_hardware_device(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retires a hardware device from the fleet."""
    return await HardwareService.remove_device(current_user.company_id, asset_id, db)


@router.post("/assets/hardware/devices/{asset_id}/test-connection", response_model=DeviceTestConnectionResponse)
async def test_device_live_connection(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceTestConnectionResponse:
    """
    Tests live communication with device or provider gateway.
    Returns online/offline status, last packet age, and telemetry diagnostics.
    """
    return await HardwareService.test_device_connection(current_user.company_id, asset_id, db)


@router.get("/assets/hardware/devices/{asset_id}/locations", response_model=DeviceLocationHistoryResponse)
async def get_device_location_history(
    asset_id: int,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(500, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceLocationHistoryResponse:
    """
    Retrieves chronological breadcrumb route history, distance travelled,
    max speed, and average speed for playback.
    """
    return await HardwareService.get_device_location_history(
        company_id=current_user.company_id,
        asset_id=asset_id,
        db=db,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )


# ===========================================================================
# 4. GPS Provider Account Management (Traccar, Teltonika, Queclink, etc.)
# ===========================================================================

@router.get("/assets/hardware/providers", response_model=List[GPSProviderAccountResponse])
async def list_gps_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[GPSProviderAccountResponse]:
    """Lists third-party GPS provider accounts connected by the company."""
    return await HardwareService.list_provider_accounts(current_user.company_id, db)


@router.post("/assets/hardware/providers", response_model=GPSProviderAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_gps_provider(
    payload: GPSProviderAccountCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GPSProviderAccountResponse:
    """Connects a third-party GPS provider account (e.g. Traccar server)."""
    return await HardwareService.create_provider_account(current_user.company_id, payload, db)


@router.post("/assets/hardware/providers/{account_id}/test", response_model=DeviceTestConnectionResponse)
async def test_gps_provider_connectivity(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DeviceTestConnectionResponse:
    """Tests connectivity to a connected GPS provider."""
    return await HardwareService.test_provider_account(current_user.company_id, account_id, db)


@router.post("/assets/hardware/providers/{account_id}/sync")
async def sync_gps_provider_devices(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Synchronizes device registry and positions from the GPS provider."""
    return await HardwareService.sync_provider_account(current_user.company_id, account_id, db)


@router.delete("/assets/hardware/providers/{account_id}")
async def delete_gps_provider(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revokes a connected GPS provider account."""
    return await HardwareService.delete_provider_account(current_user.company_id, account_id, db)


# ===========================================================================
# 5. Legacy Endpoints (Maintained for Backwards Compatibility)
# ===========================================================================

@router.post("/assets/hardware", response_model=AssetResponse)
async def add_hardware_device_legacy(
    payload: HardwareAssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssetResponse:
    """Legacy endpoint: add a new hardware device and connect it to a vehicle."""
    company_id = current_user.company_id

    # Verify vehicle ownership
    vehicle = await db.get(Vehicle, payload.vehicle_id)
    if not vehicle or vehicle.company_id != company_id:
        raise HTTPException(400, "This vehicle is not available in your fleet.")

    reg_payload = HardwareDeviceRegisterRequest(
        device_name=payload.device_name.strip(),
        connection_type=ConnectionType.DIRECT_HARDWARE.value,
        manufacturer="Unknown",
        model=payload.device_name.strip(),
        imei=payload.api_key.strip()[:15] if len(payload.api_key.strip()) >= 4 else f"DEV-{uuid.uuid4().hex[:8]}",
        vehicle_id=payload.vehicle_id,
        credentials={"api_key": payload.api_key.strip()}
    )
    dev_resp = await HardwareService.register_device(company_id, reg_payload, db)
    
    # Return as AssetResponse
    asset = await db.get(Asset, dev_resp.id)
    return AssetResponse.model_validate(asset)


@router.get("/assets", response_model=List[AssetResponse])
async def list_assets_legacy(
    installation_status: Optional[AssetInstallationStatus] = Query(None),
    operational_status: Optional[AssetOperationalStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AssetResponse]:
    """List assets scoped directly to current_user.company_id."""
    company_id = current_user.company_id

    query = (
        select(Asset)
        .where(Asset.company_id == company_id)
    )
    if installation_status:
        query = query.where(Asset.installation_status == installation_status)
    if operational_status:
        query = query.where(Asset.operational_status == operational_status)
    query = query.order_by(Asset.id.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    assets = result.scalars().all()
    return [AssetResponse.model_validate(a) for a in assets]


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset_legacy(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssetResponse:
    """Get a single asset by ID with company ownership check."""
    company_id = current_user.company_id
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.company_id == company_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(404, f"Asset {asset_id} not found")
    return AssetResponse.model_validate(asset)


@router.get("/vehicles/{vehicle_id}/assets", response_model=List[AssetResponse])
async def get_assets_by_vehicle(
    vehicle_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AssetResponse]:
    """Get assets installed on a specific vehicle."""
    company_id = current_user.company_id
    v = await db.get(Vehicle, vehicle_id)
    if not v or v.company_id != company_id:
        raise HTTPException(404, "Vehicle not found in your fleet")

    result = await db.execute(
        select(Asset)
        .where(Asset.current_vehicle_id == vehicle_id, Asset.company_id == company_id)
        .order_by(Asset.id.desc())
        .offset(offset)
        .limit(limit)
    )
    assets = result.scalars().all()
    return [AssetResponse.model_validate(a) for a in assets]


# ===========================================================================
# 6. Super-Admin Quarantine Governance
# ===========================================================================

@router.get("/admin/hardware/quarantined-assets", response_model=List[QuarantinedAssetItem])
async def list_quarantined_assets(
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_admin_permission("hardware.admin")),
) -> List[QuarantinedAssetItem]:
    """
    Returns all hardware devices held in system quarantine.
    Restricted to Super-Admins only.
    """
    return await HardwareService.list_quarantined_assets(db)


@router.post("/admin/hardware/quarantined-assets/{asset_id}/reassign", response_model=HardwareDeviceResponse)
async def reassign_quarantined_asset(
    asset_id: int,
    payload: QuarantinedAssetReassignRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    admin: AdminUser = Depends(require_admin_permission("hardware.admin")),
) -> HardwareDeviceResponse:
    """
    Reassigns a quarantined hardware device to an active tenant company and optional vehicle.
    Fully audit-logged in AdminAuditLog and AssetHistory.
    Restricted to Super-Admins only.
    """
    ip_addr = request.client.host if request.client else None
    return await HardwareService.reassign_quarantined_asset(
        asset_id=asset_id,
        payload=payload,
        admin_id=admin.id,
        admin_email=admin.email,
        db=db,
        ip_address=ip_addr
    )

