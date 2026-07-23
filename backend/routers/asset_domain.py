"""
FleetGuard — Asset Domain API Router
Provides Read-Only REST APIs for the Asset Business Domain.
(Write operations are processed asynchronously via Operational Events).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from database import get_read_uow
from infrastructure.uow import AbstractUnitOfWork
from models.asset_domain import AssetInstallationStatus, AssetOperationalStatus
from services.asset_service import AssetService
from schemas.asset_domain import AssetResponse

router = APIRouter(prefix="/v1", tags=["Asset Domain"])


@router.get("/assets", response_model=List[AssetResponse])
async def list_assets(
    installation_status: Optional[AssetInstallationStatus] = Query(None),
    operational_status: Optional[AssetOperationalStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> List[AssetResponse]:
    """List all assets with optional status filters."""
    service = AssetService(uow)
    assets = await service.search_assets(
        installation_status=installation_status, 
        operational_status=operational_status, 
        limit=limit, 
        offset=offset
    )
    return [AssetResponse.model_validate(a) for a in assets]


@router.get("/assets/search", response_model=List[AssetResponse])
async def search_assets(
    installation_status: Optional[AssetInstallationStatus] = Query(None),
    operational_status: Optional[AssetOperationalStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> List[AssetResponse]:
    """Search for assets based on criteria."""
    service = AssetService(uow)
    assets = await service.search_assets(
        installation_status=installation_status, 
        operational_status=operational_status, 
        limit=limit, 
        offset=offset
    )
    return [AssetResponse.model_validate(a) for a in assets]


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int, 
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> AssetResponse:
    """Get a single asset by internal ID."""
    service = AssetService(uow)
    asset = await service.get_asset(asset_id)
    if not asset:
        raise HTTPException(404, f"Asset {asset_id} not found")
    return AssetResponse.model_validate(asset)


@router.get("/vehicles/{vehicle_id}/assets", response_model=List[AssetResponse])
async def get_assets_by_vehicle(
    vehicle_id: int, 
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> List[AssetResponse]:
    """Get all assets currently mounted on a specific vehicle."""
    service = AssetService(uow)
    assets = await service.get_assets_by_vehicle(vehicle_id, limit=limit, offset=offset)
    return [AssetResponse.model_validate(a) for a in assets]
