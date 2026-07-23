"""
FleetGuard — Driver Domain API Router
Provides Read-Only REST APIs for the Driver Business Domain.
(Write operations are processed asynchronously via Operational Events).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database import get_db
from services.driver_service import DriverService
from schemas.driver_domain import DriverResponse

router = APIRouter(prefix="/v1", tags=["Driver Domain"])


@router.get("/drivers", response_model=List[DriverResponse])
async def list_drivers(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[DriverResponse]:
    """List all drivers with optional active filter."""
    service = DriverService(db)
    drivers = await service.search_drivers(is_active=is_active, limit=limit, offset=offset)
    return [DriverResponse.model_validate(d) for d in drivers]


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: int, 
    db: AsyncSession = Depends(get_db)
) -> DriverResponse:
    """Get a single driver by ID."""
    service = DriverService(db)
    driver = await service.get_driver(driver_id)
    if not driver:
        raise HTTPException(404, f"Driver {driver_id} not found")
    return DriverResponse.model_validate(driver)
