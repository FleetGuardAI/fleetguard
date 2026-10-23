"""
FleetGuard — Tyre Domain API Router
Provides comprehensive REST APIs for the Tyre Business Domain:
- Multi-tenant serialized tyre identity and inventory visibility
- Hardened lifecycle mutations (install, remove, rotate, retread, repair, retire)
- Wheel position tracking and collision guards
- Concurrency control and financial integrity

Security: All endpoints require authentication and are strictly scoped to the
authenticated user's company_id.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from infrastructure.uow import AbstractUnitOfWork, RepositoryRegistry
from models.tyre_domain import Tyre, TyreStatus
from models.vehicle_domain import Vehicle
from models.user import User
from services.auth_service import get_current_user
from services.tyre_service import (
    TyreService,
    TyreNotFoundError,
    InvalidTyreStateTransitionError,
    WheelPositionOccupiedError,
    OdometerRollbackError,
    VehicleNotFoundError,
)
from schemas.tyre_domain import (
    TyreResponse,
    TyreInventorySummaryResponse,
    TyreInventoryValuationResponse,
    TyreCreateRequest,
    TyreInstallRequest,
    TyreRemoveRequest,
    TyreRotateRequest,
    TyreRetreadRequest,
    TyreRepairRequest,
    TyreRetireRequest,
)

router = APIRouter(prefix="/v1", tags=["Tyre Domain"])


class SessionUoW(AbstractUnitOfWork):
    """Scoped UoW wrapping the request session."""
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repositories = RepositoryRegistry(session)

    async def commit(self):
        await self.session.flush()

    async def rollback(self):
        await self.session.rollback()


# ===========================================================================
# Read Endpoints
# ===========================================================================

@router.get("/tyres", response_model=List[TyreResponse])
async def list_tyres(
    status: Optional[TyreStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TyreResponse]:
    """
    List all tyres belonging to the tenant company.
    Includes tyres currently in storage, mounted, retreading, or retired.
    """
    company_id = current_user.company_id

    query = (
        select(Tyre)
        .outerjoin(Vehicle, Tyre.current_vehicle_id == Vehicle.id)
        .where(or_(Tyre.company_id == company_id, Vehicle.company_id == company_id))
    )
    if status:
        query = query.where(Tyre.current_status == status)
    query = query.order_by(Tyre.id.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    tyres = result.scalars().all()
    return [TyreResponse.model_validate(t) for t in tyres]


@router.get("/tyres/inventory/summary", response_model=TyreInventorySummaryResponse)
async def get_inventory_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TyreInventorySummaryResponse:
    """
    Aggregates current tyre inventory balances by lifecycle state for the company.
    Enforces invariant: Total Tyres = In Storage + Mounted + Retreading + In Repair + Retired.
    """
    company_id = current_user.company_id
    uow = SessionUoW(db)
    svc = TyreService(uow)
    summary = await svc.get_inventory_summary(company_id)
    return TyreInventorySummaryResponse(**summary)


@router.get("/tyres/inventory/valuation", response_model=TyreInventoryValuationResponse)
async def get_inventory_valuation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TyreInventoryValuationResponse:
    """
    Computes company-scoped inventory acquisition valuation.
    Separates known acquisition cost across lifecycle states.
    Explicitly reports missing/unknown-cost tyre counts without zero-fabrication.
    Reports retread and repair expenditures separately from the Expense ledger.
    """
    company_id = current_user.company_id
    uow = SessionUoW(db)
    svc = TyreService(uow)
    valuation_data = await svc.get_inventory_valuation(company_id)
    return TyreInventoryValuationResponse(**valuation_data)


@router.get("/tyres/search", response_model=List[TyreResponse])
async def search_tyres(
    status: Optional[TyreStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TyreResponse]:
    """Search for tyres belonging to the tenant company with optional status filter."""
    company_id = current_user.company_id

    query = (
        select(Tyre)
        .outerjoin(Vehicle, Tyre.current_vehicle_id == Vehicle.id)
        .where(or_(Tyre.company_id == company_id, Vehicle.company_id == company_id))
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
    """Get a single tyre by internal ID. Verifies tenant ownership."""
    company_id = current_user.company_id

    result = await db.execute(
        select(Tyre)
        .outerjoin(Vehicle, Tyre.current_vehicle_id == Vehicle.id)
        .where(
            Tyre.id == tyre_id,
            or_(Tyre.company_id == company_id, Vehicle.company_id == company_id)
        )
    )
    tyre = result.scalar_one_or_none()
    if not tyre:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Tyre {tyre_id} not found")
    return TyreResponse.model_validate(tyre)


@router.get("/vehicles/{vehicle_id}/tyres", response_model=List[TyreResponse])
async def get_tyres_by_vehicle(
    vehicle_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TyreResponse]:
    """Get all tyres currently mounted on a specific vehicle."""
    company_id = current_user.company_id

    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Vehicle {vehicle_id} not found")

    result = await db.execute(
        select(Tyre)
        .where(Tyre.current_vehicle_id == vehicle_id, Tyre.current_status == TyreStatus.INSTALLED)
        .order_by(Tyre.id.desc())
        .offset(offset)
        .limit(limit)
    )
    tyres = result.scalars().all()
    return [TyreResponse.model_validate(t) for t in tyres]


# ===========================================================================
# Lifecycle Write Endpoints
# ===========================================================================

@router.post("/tyres", response_model=TyreResponse, status_code=status.HTTP_201_CREATED)
async def register_tyre(
    payload: TyreCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TyreResponse:
    """Direct stock entry / registration of a new physical tyre into depot inventory."""
    company_id = current_user.company_id
    uow = SessionUoW(db)
    svc = TyreService(uow)
    origin_id = f"API-REG-{uuid.uuid4().hex[:8]}"
    try:
        tyre = await svc.register_tyre(payload.serial_number, payload.model_dump(), origin_id, company_id)
        await db.flush()
        return TyreResponse.model_validate(tyre)
    except InvalidTyreStateTransitionError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/tyres/{serial_number}/install", response_model=TyreResponse)
async def install_tyre(
    serial_number: str,
    payload: TyreInstallRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TyreResponse:
    """Mounts a tyre onto a vehicle at a designated wheel position."""
    company_id = current_user.company_id
    uow = SessionUoW(db)
    svc = TyreService(uow)
    origin_id = f"API-INS-{uuid.uuid4().hex[:8]}"
    try:
        tyre = await svc.install_tyre(serial_number, payload.model_dump(), origin_id, company_id)
        await db.flush()
        return TyreResponse.model_validate(tyre)
    except TyreNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except VehicleNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except WheelPositionOccupiedError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidTyreStateTransitionError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/tyres/{serial_number}/remove", response_model=TyreResponse)
async def remove_tyre(
    serial_number: str,
    payload: TyreRemoveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TyreResponse:
    """Removes an installed tyre from a vehicle and records accumulated distance run."""
    company_id = current_user.company_id
    uow = SessionUoW(db)
    svc = TyreService(uow)
    origin_id = f"API-REM-{uuid.uuid4().hex[:8]}"
    try:
        tyre = await svc.remove_tyre(serial_number, payload.model_dump(), origin_id, company_id)
        await db.flush()
        return TyreResponse.model_validate(tyre)
    except TyreNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except OdometerRollbackError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidTyreStateTransitionError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/tyres/{serial_number}/rotate", response_model=TyreResponse)
async def rotate_tyre(
    serial_number: str,
    payload: TyreRotateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TyreResponse:
    """Rotates a tyre to a new wheel position on the same vehicle."""
    company_id = current_user.company_id
    uow = SessionUoW(db)
    svc = TyreService(uow)
    origin_id = f"API-ROT-{uuid.uuid4().hex[:8]}"
    try:
        tyre = await svc.rotate_tyre(serial_number, payload.model_dump(), origin_id, company_id)
        await db.flush()
        return TyreResponse.model_validate(tyre)
    except TyreNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except WheelPositionOccupiedError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))
    except InvalidTyreStateTransitionError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/tyres/{serial_number}/retread", response_model=TyreResponse)
async def retread_tyre(
    serial_number: str,
    payload: TyreRetreadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TyreResponse:
    """Processes retreading completion or casing rejection for a tyre."""
    company_id = current_user.company_id
    uow = SessionUoW(db)
    svc = TyreService(uow)
    origin_id = f"API-RET-{uuid.uuid4().hex[:8]}"
    try:
        tyre = await svc.retread_tyre(serial_number, payload.model_dump(), origin_id, company_id)
        await db.flush()
        return TyreResponse.model_validate(tyre)
    except TyreNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidTyreStateTransitionError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/tyres/{serial_number}/repair", response_model=TyreResponse)
async def repair_tyre(
    serial_number: str,
    payload: TyreRepairRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TyreResponse:
    """Records a tyre repair (puncture, vulcanizing, patch) and expense."""
    company_id = current_user.company_id
    uow = SessionUoW(db)
    svc = TyreService(uow)
    origin_id = f"API-REP-{uuid.uuid4().hex[:8]}"
    try:
        tyre = await svc.repair_tyre(serial_number, payload.model_dump(), origin_id, company_id)
        await db.flush()
        return TyreResponse.model_validate(tyre)
    except TyreNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidTyreStateTransitionError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/tyres/{serial_number}/retire", response_model=TyreResponse)
async def retire_tyre(
    serial_number: str,
    payload: TyreRetireRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TyreResponse:
    """Permanently decommissions / scraps a physical tyre."""
    company_id = current_user.company_id
    uow = SessionUoW(db)
    svc = TyreService(uow)
    origin_id = f"API-SCRAP-{uuid.uuid4().hex[:8]}"
    try:
        tyre = await svc.retire_tyre(serial_number, payload.model_dump(), origin_id, company_id)
        await db.flush()
        return TyreResponse.model_validate(tyre)
    except TyreNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvalidTyreStateTransitionError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
