"""
FleetGuard — Vehicle Domain API Router
Provides Read-Only REST APIs for the Vehicle Business Domain.
(Write operations are processed asynchronously via Operational Events).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from database import get_read_uow
from infrastructure.uow import AbstractUnitOfWork
from services.vehicle_service import VehicleService
from schemas.vehicle_domain import VehicleResponse

router = APIRouter(prefix="/v1", tags=["Vehicle Domain"])


@router.get("/vehicles", response_model=List[VehicleResponse])
async def list_vehicles(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> List[VehicleResponse]:
    """List all vehicles with optional active filter."""
    service = VehicleService(uow)
    vehicles = await service.search_vehicles(is_active=is_active, limit=limit, offset=offset)
    return [VehicleResponse.model_validate(v) for v in vehicles]


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: int, 
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> VehicleResponse:
    """Get a single vehicle by ID."""
    service = VehicleService(uow)
    vehicle = await service.get_vehicle(vehicle_id)
    if not vehicle:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")
    return VehicleResponse.model_validate(vehicle)
