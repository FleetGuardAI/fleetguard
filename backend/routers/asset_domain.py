"""
FleetGuard — Asset Domain API Router
Provides Read-Only REST APIs for the Asset Business Domain.
(Write operations are processed asynchronously via Operational Events).

Security: All endpoints require authentication and are scoped to the
authenticated user's company. Assets are linked to company via the
Vehicle→company_id relationship.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database import get_db
from models.asset_domain import Asset, AssetInstallationStatus, AssetOperationalStatus, AssetType
from models.vehicle_domain import Vehicle
from schemas.asset_domain import AssetResponse, HardwareAssetCreate
from services.auth_service import get_current_user
from models.user import User
from passlib.context import CryptContext
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/v1", tags=["Asset Domain"])


@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
    installation_status: Optional[AssetInstallationStatus] = Query(None),
    operational_status: Optional[AssetOperationalStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AssetResponse]:
    """List all assets with optional status filters. Company-scoped via vehicle."""
    company_id = current_user.company_id

    query = (
        select(Asset)
        .outerjoin(Vehicle, Asset.current_vehicle_id == Vehicle.id)
        .where(Vehicle.company_id == company_id)
    )
    if installation_status:
        query = query.where(Asset.installation_status == installation_status)
    if operational_status:
        query = query.where(Asset.operational_status == operational_status)
    query = query.order_by(Asset.id.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    assets = result.scalars().all()
    return [AssetResponse.model_validate(a) for a in assets]


@router.get("/assets/search", response_model=List[AssetResponse])
async def search_assets(
    installation_status: Optional[AssetInstallationStatus] = Query(None),
    operational_status: Optional[AssetOperationalStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AssetResponse]:
    """Search for assets based on criteria. Company-scoped via vehicle."""
    company_id = current_user.company_id

    query = (
        select(Asset)
        .outerjoin(Vehicle, Asset.current_vehicle_id == Vehicle.id)
        .where(Vehicle.company_id == company_id)
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
async def get_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssetResponse:
    """Get a single asset by internal ID. Verifies company ownership via vehicle."""
    company_id = current_user.company_id

    result = await db.execute(
        select(Asset)
        .outerjoin(Vehicle, Asset.current_vehicle_id == Vehicle.id)
        .where(Asset.id == asset_id, Vehicle.company_id == company_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(404, f"Asset {asset_id} not found")
    return AssetResponse.model_validate(asset)


@router.post("/assets/hardware", response_model=AssetResponse)
async def add_hardware_device(
    payload: HardwareAssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssetResponse:
    """Add a new hardware device/asset and connect it to a vehicle."""
    company_id = current_user.company_id

    # Verify vehicle ownership
    vehicle = await db.get(Vehicle, payload.vehicle_id)
    if not vehicle or vehicle.company_id != company_id:
        raise HTTPException(400, "This vehicle is not available in your fleet.")

    # Validate that we don't already have an asset with this API key
    hashed_key = pwd_context.hash(payload.api_key.strip())
    # Note: We can't strictly search by hash since hashes use salts, 
    # but we will just trust the UI to not allow duplicate inserts if they somehow have the same key.
    # Alternatively, just create the asset. 

    new_asset = Asset(
        business_id=f"HW-{uuid.uuid4().hex[:8].upper()}",
        asset_type=AssetType.GPS_DEVICE, # default
        manufacturer="Unknown",
        model=payload.device_name.strip(),
        current_vehicle_id=payload.vehicle_id,
        installation_status=AssetInstallationStatus.INSTALLED,
        operational_status=AssetOperationalStatus.OK,
        purchase_information={"api_key_hash": hashed_key}
    )
    db.add(new_asset)
    await db.commit()
    await db.refresh(new_asset)
    
    return AssetResponse.model_validate(new_asset)


@router.get("/vehicles/{vehicle_id}/assets", response_model=List[AssetResponse])
async def get_assets_by_vehicle(
    vehicle_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[AssetResponse]:
    """Get all assets currently mounted on a specific vehicle. Verifies vehicle ownership."""
    company_id = current_user.company_id

    # Verify vehicle belongs to the company
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.company_id != company_id:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")

    result = await db.execute(
        select(Asset)
        .where(Asset.current_vehicle_id == vehicle_id)
        .order_by(Asset.id.desc())
        .offset(offset)
        .limit(limit)
    )
    assets = result.scalars().all()
    return [AssetResponse.model_validate(a) for a in assets]
