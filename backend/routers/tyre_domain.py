"""
FleetGuard — Tyre Domain API Router
Provides Read-Only REST APIs for the Tyre Business Domain.
(Write operations are processed asynchronously via Operational Events).

Security: All endpoints require authentication and are scoped to the
authenticated user's company. Tyres are linked to company via the
Vehicle→company_id relationship.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database import get_db
from models.tyre_domain import Tyre, TyreStatus
from models.vehicle_domain import Vehicle
from schemas.tyre_domain import TyreResponse
from services.auth_service import get_current_user
from models.user import User

router = APIRouter(prefix="/v1", tags=["Tyre Domain"])


@router.get("/tyres", response_model=List[TyreResponse])
async def list_tyres(
    status: Optional[TyreStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TyreResponse]:
    """List all tyres with optional status filter. Company-scoped via vehicle."""
    company_id = current_user.company_id

    query = (
        select(Tyre)
        .outerjoin(Vehicle, Tyre.current_vehicle_id == Vehicle.id)
        .where(Vehicle.company_id == company_id)
    )
    if status:
        query = query.where(Tyre.current_status == status)
    query = query.order_by(Tyre.id.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    tyres = result.scalars().all()
    return [TyreResponse.model_validate(t) for t in tyres]


@router.get("/tyres/search", response_model=List[TyreResponse])
async def search_tyres(
    status: Optional[TyreStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TyreResponse]:
    """Search for tyres based on criteria. Company-scoped via vehicle."""
    company_id = current_user.company_id

    query = (
        select(Tyre)
        .outerjoin(Vehicle, Tyre.current_vehicle_id == Vehicle.id)
        .where(Vehicle.company_id == company_id)
    )
    if status:
        query = query.where(Tyre.current_status == status)
    query = query.order_by(Tyre.id.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    tyres = result.scalars().all()
    return [TyreResponse.model_validate(t) for t in tyres]


@router.get("/tyres/{tyre_id}", response_model=TyreResponse)
async def get_tyre(
    tyre_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TyreResponse:
    """Get a single tyre by internal ID. Verifies company ownership via vehicle."""
    company_id = current_user.company_id

    result = await db.execute(
        select(Tyre)
        .outerjoin(Vehicle, Tyre.current_vehicle_id == Vehicle.id)
        .where(Tyre.id == tyre_id, Vehicle.company_id == company_id)
    )
    tyre = result.scalar_one_or_none()
    if not tyre:
        raise HTTPException(404, f"Tyre {tyre_id} not found")
    return TyreResponse.model_validate(tyre)


@router.get("/vehicles/{vehicle_id}/tyres", response_model=List[TyreResponse])
async def get_tyres_by_vehicle(
    vehicle_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TyreResponse]:
    """Get all tyres currently mounted on a specific vehicle. Verifies vehicle ownership."""
    company_id = current_user.company_id

    # Verify vehicle belongs to the company
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.company_id != company_id:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")

    result = await db.execute(
        select(Tyre)
        .where(Tyre.current_vehicle_id == vehicle_id)
        .order_by(Tyre.id.desc())
        .offset(offset)
        .limit(limit)
    )
    tyres = result.scalars().all()
    return [TyreResponse.model_validate(t) for t in tyres]
