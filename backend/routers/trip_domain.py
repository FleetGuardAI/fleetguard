"""
FleetGuard — Trip Domain API Router
Provides Read-Only REST APIs for the Trip Business Domain.
(Write operations are processed asynchronously via Operational Events).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from database import get_read_uow, get_db
from infrastructure.uow import AbstractUnitOfWork
from models.trip_domain import TripStatus
from services.trip_service import TripService
from services.trip_intelligence_service import TripIntelligenceService
from schemas.trip_domain import TripResponse, TripCreate, TripUpdated
from schemas.trip_intelligence import TripIntelligenceResponse
from services.auth_service import get_current_user
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

router = APIRouter(prefix="/v1", tags=["Trip Domain"])


@router.get("/trips", response_model=List[TripResponse])
async def list_trips(
    search: Optional[str] = Query(None),
    status: Optional[TripStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> List[TripResponse]:
    """List all trips with optional status and search filters."""
    service = TripService(uow)
    trips = await service.search_trips(status=status, limit=limit, offset=offset, company_id=current_user.company_id, search=search)
    return [TripResponse.model_validate(t) for t in trips]

@router.post("/trips", response_model=TripResponse, status_code=201)
async def create_trip(
    payload: TripCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TripResponse:
    """Create a new trip explicitly (bypass event queue for sync operations)."""
    from models.vehicle_domain import Vehicle
    from models.driver_domain import Driver
    from models.trip_domain import Trip, TripStatus

    vehicle = await db.get(Vehicle, payload.vehicle_id)
    driver = await db.get(Driver, payload.driver_id)

    if not vehicle or vehicle.company_id != current_user.company_id:
        raise HTTPException(400, "Invalid vehicle_id")
    if not driver or driver.company_id != current_user.company_id:
        raise HTTPException(400, "Invalid driver_id")

    trip_id = f"TRP-{str(uuid.uuid4())[:8].upper()}"

    trip = Trip(
        trip_id=trip_id,
        status=TripStatus.CREATED,
        origin_location=payload.origin_location,
        destination_location=payload.destination_location,
        planned_distance=payload.planned_distance,
        planned_start_time=payload.planned_start_time,
        planned_end_time=payload.planned_end_time,
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
        company_id=current_user.company_id,
        origin_type="rest_api"
    )
    db.add(trip)
    await db.commit()
    await db.refresh(trip)

    return TripResponse.model_validate(trip)


@router.get("/trips/search", response_model=List[TripResponse])
async def search_trips(
    search: Optional[str] = Query(None),
    status: Optional[TripStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> List[TripResponse]:
    """Search for trips based on criteria."""
    service = TripService(uow)
    trips = await service.search_trips(status=status, limit=limit, offset=offset, company_id=current_user.company_id, search=search)
    return [TripResponse.model_validate(t) for t in trips]


@router.get("/trips/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: int, 
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> TripResponse:
    """Get a single trip by ID."""
    service = TripService(uow)
    trip = await service.get_trip(trip_id)
    if not trip or trip.company_id != current_user.company_id:
        raise HTTPException(404, f"Trip {trip_id} not found")
    return TripResponse.model_validate(trip)


@router.patch("/trips/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: int,
    payload: TripUpdated,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TripResponse:
    from models.trip_domain import Trip
    trip = await db.get(Trip, trip_id)
    if not trip or trip.company_id != current_user.company_id:
        raise HTTPException(404, f"Trip {trip_id} not found")
    
    if payload.status is not None:
        trip.status = payload.status
    if payload.vehicle_id is not None:
        trip.vehicle_id = payload.vehicle_id
    if payload.driver_id is not None:
        trip.driver_id = payload.driver_id
        
    await db.commit()
    await db.refresh(trip)
    return TripResponse.model_validate(trip)


@router.get("/trips/{trip_id}/intelligence", response_model=TripIntelligenceResponse)
async def get_trip_intelligence(
    trip_id: int,
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user),
) -> TripIntelligenceResponse:
    """
    Get Trip Intelligence analysis for a specific trip.
    Returns profitability, cost breakdown, efficiency score,
    anomaly insights, historical comparisons, and recommendations.
    Company-scoped.
    """
    trip_service = TripService(uow)
    trip = await trip_service.get_trip(trip_id)
    if not trip or trip.company_id != current_user.company_id:
        raise HTTPException(404, f"Trip {trip_id} not found")

    intelligence_service = TripIntelligenceService(uow)
    return await intelligence_service.compute_intelligence(trip)

@router.get("/vehicles/{vehicle_id}/trips", response_model=List[TripResponse])
async def get_trips_by_vehicle(
    vehicle_id: int, 
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> List[TripResponse]:
    """Get all trips associated with a specific vehicle."""
    service = TripService(uow)
    trips = await service.get_trips_by_vehicle(vehicle_id, limit=limit, offset=offset, company_id=current_user.company_id)
    return [TripResponse.model_validate(t) for t in trips]


@router.get("/drivers/{driver_id}/trips", response_model=List[TripResponse])
async def get_trips_by_driver(
    driver_id: int, 
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> List[TripResponse]:
    """Get all trips associated with a specific driver."""
    service = TripService(uow)
    trips = await service.get_trips_by_driver(driver_id, limit=limit, offset=offset, company_id=current_user.company_id)
    return [TripResponse.model_validate(t) for t in trips]
