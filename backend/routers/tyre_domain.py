"""
FleetGuard — Tyre Domain API Router
Provides Read-Only REST APIs for the Tyre Business Domain.
(Write operations are processed asynchronously via Operational Events).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from database import get_read_uow
from infrastructure.uow import AbstractUnitOfWork
from models.tyre_domain import TyreStatus
from services.tyre_service import TyreService
from schemas.tyre_domain import TyreResponse

router = APIRouter(prefix="/v1", tags=["Tyre Domain"])


@router.get("/tyres", response_model=List[TyreResponse])
async def list_tyres(
    status: Optional[TyreStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> List[TyreResponse]:
    """List all tyres with optional status filter."""
    service = TyreService(uow)
    tyres = await service.search_tyres(status=status, limit=limit, offset=offset)
    return [TyreResponse.model_validate(t) for t in tyres]


@router.get("/tyres/search", response_model=List[TyreResponse])
async def search_tyres(
    status: Optional[TyreStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> List[TyreResponse]:
    """Search for tyres based on criteria."""
    service = TyreService(uow)
    tyres = await service.search_tyres(status=status, limit=limit, offset=offset)
    return [TyreResponse.model_validate(t) for t in tyres]


@router.get("/tyres/{tyre_id}", response_model=TyreResponse)
async def get_tyre(
    tyre_id: int, 
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> TyreResponse:
    """Get a single tyre by internal ID."""
    service = TyreService(uow)
    tyre = await service.get_tyre(tyre_id)
    if not tyre:
        raise HTTPException(404, f"Tyre {tyre_id} not found")
    return TyreResponse.model_validate(tyre)


@router.get("/vehicles/{vehicle_id}/tyres", response_model=List[TyreResponse])
async def get_tyres_by_vehicle(
    vehicle_id: int, 
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> List[TyreResponse]:
    """Get all tyres currently mounted on a specific vehicle."""
    service = TyreService(uow)
    tyres = await service.get_tyres_by_vehicle(vehicle_id, limit=limit, offset=offset)
    return [TyreResponse.model_validate(t) for t in tyres]
