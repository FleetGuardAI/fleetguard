"""
FleetGuard — Trip Domain API Router
Provides Read-Only REST APIs for the Trip Business Domain.
(Write operations are processed asynchronously via Operational Events).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from database import get_read_uow
from infrastructure.uow import AbstractUnitOfWork
from models.trip_domain import TripStatus
from services.trip_service import TripService
from schemas.trip_domain import TripResponse

router = APIRouter(prefix="/v1", tags=["Trip Domain"])


@router.get("/trips", response_model=List[TripResponse])
async def list_trips(
    status: Optional[TripStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> List[TripResponse]:
    """List all trips with optional status filter."""
    service = TripService(uow)
    trips = await service.search_trips(status=status, limit=limit, offset=offset)
    return [TripResponse.model_validate(t) for t in trips]


@router.get("/trips/search", response_model=List[TripResponse])
async def search_trips(
    status: Optional[TripStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> List[TripResponse]:
    """Search for trips based on criteria."""
    service = TripService(uow)
    trips = await service.search_trips(status=status, limit=limit, offset=offset)
    return [TripResponse.model_validate(t) for t in trips]


@router.get("/trips/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: int, 
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> TripResponse:
    """Get a single trip by ID."""
    service = TripService(uow)
    trip = await service.get_trip(trip_id)
    if not trip:
        raise HTTPException(404, f"Trip {trip_id} not found")
    return TripResponse.model_validate(trip)


@router.get("/vehicles/{vehicle_id}/trips", response_model=List[TripResponse])
async def get_trips_by_vehicle(
    vehicle_id: int, 
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> List[TripResponse]:
    """Get all trips associated with a specific vehicle."""
    service = TripService(uow)
    trips = await service.get_trips_by_vehicle(vehicle_id, limit=limit, offset=offset)
    return [TripResponse.model_validate(t) for t in trips]


@router.get("/drivers/{driver_id}/trips", response_model=List[TripResponse])
async def get_trips_by_driver(
    driver_id: int, 
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
) -> List[TripResponse]:
    """Get all trips associated with a specific driver."""
    service = TripService(uow)
    trips = await service.get_trips_by_driver(driver_id, limit=limit, offset=offset)
    return [TripResponse.model_validate(t) for t in trips]
