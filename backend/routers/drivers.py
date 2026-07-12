"""
FleetGuard — Drivers API Router
CRUD operations and risk scoring for drivers.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database import get_db
from models.driver import Driver
from schemas.driver import DriverCreate, DriverUpdate, DriverResponse

router = APIRouter(prefix="/drivers", tags=["Drivers"])


@router.get("", response_model=list[DriverResponse])
async def list_drivers(
    is_active: Optional[bool] = Query(None),
    min_risk: Optional[float] = Query(None, ge=0, le=100, description="Minimum risk score filter"),
    sort_by: str = Query("name", description="Sort by: name, risk_score, rating"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[DriverResponse]:
    """List all drivers with optional filters and sorting."""
    query = select(Driver)

    if is_active is not None:
        query = query.where(Driver.is_active == is_active)

    if min_risk is not None:
        query = query.where(Driver.risk_score >= min_risk)

    # Dynamic sorting
    sort_column = {
        "name": Driver.name,
        "risk_score": Driver.risk_score.desc(),
        "rating": Driver.rating.desc(),
    }.get(sort_by, Driver.name)

    query = query.order_by(sort_column).offset(offset).limit(limit)
    result = await db.execute(query)
    drivers = result.scalars().all()

    return [DriverResponse.model_validate(d) for d in drivers]


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(driver_id: int, db: AsyncSession = Depends(get_db)) -> DriverResponse:
    """Get a single driver by ID."""
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(404, f"Driver {driver_id} not found")
    return DriverResponse.model_validate(driver)


@router.post("", response_model=DriverResponse, status_code=201)
async def create_driver(
    payload: DriverCreate,
    db: AsyncSession = Depends(get_db),
) -> DriverResponse:
    """Register a new driver."""
    # Check for duplicate phone number
    existing = await db.execute(
        select(Driver).where(Driver.phone_number == payload.phone_number)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Driver with phone {payload.phone_number} already exists")

    driver = Driver(
        name=payload.name,
        phone_number=payload.phone_number,
        avatar_url=payload.avatar_url,
    )
    db.add(driver)
    await db.flush()
    await db.refresh(driver)

    return DriverResponse.model_validate(driver)


@router.patch("/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: int,
    payload: DriverUpdate,
    db: AsyncSession = Depends(get_db),
) -> DriverResponse:
    """Update driver information."""
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(404, f"Driver {driver_id} not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(driver, field, value)

    await db.flush()
    await db.refresh(driver)
    return DriverResponse.model_validate(driver)
