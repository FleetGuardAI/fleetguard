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
from schemas.pre_trip_intelligence import PreTripIntelligenceResponse, PreTripEvaluateRequest
from schemas.live_trip_intelligence import LiveTripIntelligenceResponse
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

    vehicle = None
    if payload.vehicle_id:
        vehicle = await db.get(Vehicle, payload.vehicle_id)
        if not vehicle or vehicle.company_id != current_user.company_id:
            raise HTTPException(400, "Invalid vehicle_id")
            
    driver = None
    if payload.driver_id:
        driver = await db.get(Driver, payload.driver_id)
        if not driver or driver.company_id != current_user.company_id:
            raise HTTPException(400, "Invalid driver_id")

    trip_id = f"TRP-{str(uuid.uuid4())[:8].upper()}"

    trip = Trip(
        trip_id=trip_id,
        status=TripStatus.CREATED,
        origin_location=payload.origin_location,
        origin_lat=payload.origin_lat,
        origin_lng=payload.origin_lng,
        origin_place_id=payload.origin_place_id,
        origin_address=payload.origin_address,
        
        destination_location=payload.destination_location,
        destination_lat=payload.destination_lat,
        destination_lng=payload.destination_lng,
        destination_place_id=payload.destination_place_id,
        destination_address=payload.destination_address,
        
        route_distance_km=payload.route_distance_km,
        route_duration_hours=payload.route_duration_hours,
        route_toll_estimate=payload.route_toll_estimate,
        route_provider=payload.route_provider,
        route_polyline=payload.route_polyline,
        
        planned_distance=payload.planned_distance,
        planned_start_time=payload.planned_start_time,
        planned_end_time=payload.planned_end_time,
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
        company_id=current_user.company_id,
        revenue=payload.revenue,
        planned_cost=payload.planned_cost,
        planned_fuel_liters=payload.planned_fuel_liters,
        cargo_weight=payload.cargo_weight,
        origin_type="rest_api"
    )
    
    # Run Pre-Trip Intelligence to capture snapshot
    try:
        from services.pre_trip_intelligence import PreTripIntelligenceService
        from schemas.pre_trip_intelligence import PreTripEvaluateRequest
        
        pre_req = PreTripEvaluateRequest(
            vehicle_id=payload.vehicle_id,
            driver_id=payload.driver_id,
            origin_location=payload.origin_location,
            destination_location=payload.destination_location,
            origin_lat=payload.origin_lat,
            origin_lng=payload.origin_lng,
            destination_lat=payload.destination_lat,
            destination_lng=payload.destination_lng,
            route_distance_km=payload.route_distance_km,
            route_duration_hours=payload.route_duration_hours,
            planned_distance=payload.planned_distance,
            planned_start_time=payload.planned_start_time,
            planned_end_time=payload.planned_end_time,
            revenue=payload.revenue,
            planned_cost=payload.planned_cost,
            planned_fuel_liters=payload.planned_fuel_liters,
            cargo_weight=payload.cargo_weight
        )
        
        pre_service = PreTripIntelligenceService(db)
        eval_resp = await pre_service.evaluate_trip(pre_req, current_user.company_id)
        
        trip.expected_revenue = eval_resp.expected_revenue
        trip.expected_cost = eval_resp.expected_total_cost
        trip.expected_profit = eval_resp.expected_profit
        trip.expected_margin = eval_resp.expected_margin_pct
        trip.recommendation_decision = eval_resp.recommendation.value
        trip.recommendation_at = eval_resp.calculated_at
        trip.intelligence_version = eval_resp.intelligence_version
        trip.confidence_level = eval_resp.confidence_level.value
        trip.risk_level = eval_resp.risk_level.value
        trip.intelligence_snapshot = eval_resp.model_dump(mode='json')
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to calculate pre-trip intelligence: {e}")
        
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


@router.post("/trips/intelligence/evaluate", response_model=PreTripIntelligenceResponse)
async def evaluate_trip_intelligence(
    payload: PreTripEvaluateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PreTripIntelligenceResponse:
    """
    Evaluate a potential trip before creation to determine economics, risk, and TAKE/REVIEW/AVOID decision.
    """
    from services.pre_trip_intelligence import PreTripIntelligenceService
    service = PreTripIntelligenceService(db)
    return await service.evaluate_trip(payload, current_user.company_id)


@router.get("/trips/{trip_id}/intelligence/live", response_model=LiveTripIntelligenceResponse)
async def get_live_trip_intelligence(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LiveTripIntelligenceResponse:
    """
    Get live health (ON_TRACK/AT_RISK/CRITICAL) and projected profitability for an IN_PROGRESS trip.
    """
    from models.trip_domain import Trip
    from services.live_trip_intelligence import LiveTripIntelligenceService
    
    trip = await db.get(Trip, trip_id)
    if not trip or trip.company_id != current_user.company_id:
        raise HTTPException(404, f"Trip {trip_id} not found")
        
    service = LiveTripIntelligenceService(db)
    return await service.compute_live_health(trip)


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

@router.get("/trips/{trip_id}/intelligence/snapshot", response_model=PreTripIntelligenceResponse)
async def get_trip_intelligence_snapshot(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PreTripIntelligenceResponse:
    """
    Get the pre-trip intelligence snapshot that was saved when the trip was created.
    """
    from models.trip_domain import Trip
    trip = await db.get(Trip, trip_id)
    if not trip or trip.company_id != current_user.company_id:
        raise HTTPException(404, f"Trip {trip_id} not found")
        
    if not trip.intelligence_snapshot:
        raise HTTPException(404, f"No intelligence snapshot available for Trip {trip_id}")
        
    return PreTripIntelligenceResponse(**trip.intelligence_snapshot)

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
