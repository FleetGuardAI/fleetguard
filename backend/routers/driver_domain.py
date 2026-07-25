"""
FleetGuard — Driver Domain API Router
Provides REST APIs for Driver Business Domain CRUD operations.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, get_read_uow
from infrastructure.uow import AbstractUnitOfWork
from services.driver_service import DriverService
from models.driver_domain import Driver, DriverStatus
from models.operational_event import OperationalEvent, EventType, EntityType, CaptureMethod
from schemas.driver_domain import DriverResponse, DriverCreate, DriverUpdated

router = APIRouter(prefix="/v1", tags=["Driver Domain"])


@router.get("/drivers", response_model=List[DriverResponse])
async def list_drivers(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> List[DriverResponse]:
    """List all drivers with optional active filter."""
    service = DriverService(uow)
    drivers = await service.search_drivers(is_active=is_active, limit=limit, offset=offset)
    return [DriverResponse.model_validate(d) for d in drivers]


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: int, 
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> DriverResponse:
    """Get a single driver by ID."""
    service = DriverService(uow)
    driver = await service.get_driver(driver_id)
    if not driver:
        raise HTTPException(404, f"Driver {driver_id} not found")
    return DriverResponse.model_validate(driver)


@router.post("/drivers", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    payload: DriverCreate,
    db: AsyncSession = Depends(get_db),
) -> DriverResponse:
    """Register a new driver in the database."""
    # Check if driver with phone already exists
    existing = await db.execute(select(Driver).where(Driver.phone_number == payload.phone_number))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Driver with phone number {payload.phone_number} is already registered."
        )

    driver = Driver(
        name=payload.name,
        phone_number=payload.phone_number,
        avatar_url=payload.avatar_url,
        employee_id=payload.employee_id,
        license_number=payload.license_number,
        status=DriverStatus.ACTIVE,
        origin_type="rest_api",
    )
    db.add(driver)
    await db.commit()
    await db.refresh(driver)

    # Log operational event for auditability
    event = OperationalEvent(
        event_type=EventType.DRIVER_REGISTERED,
        entity_type=EntityType.DRIVER,
        entity_id=driver.phone_number,
        occurred_at=datetime.now(timezone.utc),
        capture_method=CaptureMethod.API_INTEGRATION,
        payload={"name": driver.name, "phone_number": driver.phone_number},
    )
    db.add(event)
    await db.commit()

    return DriverResponse.model_validate(driver)


@router.patch("/drivers/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: int,
    payload: DriverUpdated,
    db: AsyncSession = Depends(get_db),
) -> DriverResponse:
    """Update driver profile details."""
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(404, f"Driver {driver_id} not found")

    if payload.name is not None:
        driver.name = payload.name
    if payload.phone_number is not None:
        driver.phone_number = payload.phone_number
    if payload.avatar_url is not None:
        driver.avatar_url = payload.avatar_url

    await db.commit()
    await db.refresh(driver)
    return DriverResponse.model_validate(driver)


@router.delete("/drivers/{driver_id}", status_code=status.HTTP_200_OK)
async def delete_driver(
    driver_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Archive/delete a driver."""
    driver = await db.get(Driver, driver_id)
    if not driver:
        raise HTTPException(404, f"Driver {driver_id} not found")

    await db.delete(driver)
    await db.commit()
    return {"message": f"Driver {driver_id} deleted successfully"}
