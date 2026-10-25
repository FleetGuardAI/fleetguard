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
from services.auth_service import get_current_user, requires_role
from models.user import User, UserRole
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
    from services.eta_service import EtaService
    service = TripService(uow)
    trips = await service.search_trips(status=status, limit=limit, offset=offset, company_id=current_user.company_id, search=search)
    
    eta_session = getattr(uow, "session", getattr(uow, "_session", None))
    eta_service = EtaService(eta_session) if eta_session else None
    response_list = []
    for t in trips:
        trip_resp = TripResponse.model_validate(t)
        if t.status == TripStatus.IN_PROGRESS and eta_service:
            try:
                enrichment = await eta_service.enrich_trip_response(t)
                trip_resp.estimated_arrival_time = enrichment.get("estimated_arrival_time")
            except Exception as e:
                pass
        response_list.append(trip_resp)
        
    return response_list

@router.post("/trips", response_model=TripResponse, status_code=201)
async def create_trip(
    payload: TripCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TripResponse:
    """Create a new trip explicitly with assignment validation and operational event emission."""
    from models.vehicle_domain import Vehicle, VehicleStatus
    from models.driver_domain import Driver, DriverStatus
    from models.trip_domain import Trip, TripStatus
    from services.trip_service import create_trip_operational_event
    from services.dispatch_suitability_service import DispatchSuitabilityService
    from models.operational_event import EventType
    from sqlalchemy import select

    if payload.vehicle_id or payload.driver_id or payload.cargo_weight or payload.required_vehicle_class or payload.required_driver_qualification:
        suitability_service = DispatchSuitabilityService(db)
        suit_res = await suitability_service.evaluate_dispatch_suitability(
            company_id=current_user.company_id,
            vehicle_id=payload.vehicle_id,
            driver_id=payload.driver_id,
            planned_start=payload.planned_start_time,
            planned_end=payload.planned_end_time,
            route_distance_km=payload.route_distance_km or payload.planned_distance,
            cargo_weight=payload.cargo_weight,
            cargo_category=payload.cargo_category,
            required_vehicle_class=payload.required_vehicle_class,
            required_driver_qualification=payload.required_driver_qualification,
            cargo_temperature_required=payload.cargo_temperature_required,
        )
        if suit_res.hard_failures:
            raise HTTPException(400, "; ".join(suit_res.hard_failures))
            
    # Validate required receiver fields if any receiver info is provided
    has_receiver_info = any([
        payload.receiver_name, payload.receiver_phone, payload.receiver_company,
        payload.receiver_address, payload.receiver_city, payload.receiver_state,
        payload.receiver_pincode, payload.receiver_notes
    ])
    if has_receiver_info:
        if not payload.receiver_name:
            raise HTTPException(400, "Receiver Name is required")
        if not payload.receiver_phone:
            raise HTTPException(400, "Receiver Phone Number is required")
        if not payload.receiver_address:
            raise HTTPException(400, "Receiver Address is required")
        if not payload.receiver_city:
            raise HTTPException(400, "Receiver City is required")
        if not payload.receiver_pincode:
            raise HTTPException(400, "Receiver Pincode is required")

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
        cargo_category=payload.cargo_category or "GENERAL",
        required_vehicle_class=payload.required_vehicle_class,
        required_driver_qualification=payload.required_driver_qualification,
        cargo_temperature_required=payload.cargo_temperature_required or False,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        customer_contact_person=payload.customer_contact_person,
        instructions=payload.instructions,
        receiver_name=payload.receiver_name,
        receiver_phone=payload.receiver_phone,
        receiver_company=payload.receiver_company,
        receiver_address=payload.receiver_address,
        receiver_city=payload.receiver_city,
        receiver_state=payload.receiver_state,
        receiver_pincode=payload.receiver_pincode,
        receiver_notes=payload.receiver_notes,
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
            cargo_weight=payload.cargo_weight,
            cargo_category=payload.cargo_category,
            required_vehicle_class=payload.required_vehicle_class,
            required_driver_qualification=payload.required_driver_qualification,
            cargo_temperature_required=payload.cargo_temperature_required
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
    
    # Authoritative OperationalEvent emissions
    event_created = create_trip_operational_event(
        company_id=current_user.company_id,
        event_type=EventType.TRIP_CREATED,
        trip_business_id=trip.trip_id,
        payload={
            "origin_location": trip.origin_location,
            "destination_location": trip.destination_location,
            "vehicle_id": trip.vehicle_id,
            "driver_id": trip.driver_id,
            "planned_distance": trip.planned_distance,
            "revenue": trip.revenue,
            "planned_cost": trip.planned_cost,
        },
        created_by=str(current_user.id)
    )
    db.add(event_created)

    if payload.driver_id:
        event_driver = create_trip_operational_event(
            company_id=current_user.company_id,
            event_type=EventType.TRIP_DRIVER_ASSIGNED,
            trip_business_id=trip.trip_id,
            payload={"driver_id": payload.driver_id},
            created_by=str(current_user.id)
        )
        db.add(event_driver)

    if payload.vehicle_id:
        event_vehicle = create_trip_operational_event(
            company_id=current_user.company_id,
            event_type=EventType.TRIP_VEHICLE_ASSIGNED,
            trip_business_id=trip.trip_id,
            payload={"vehicle_id": payload.vehicle_id},
            created_by=str(current_user.id)
        )
        db.add(event_vehicle)
    
    if payload.driver_id:
        from models.driver_domain import Driver
        from models.notification import Notification, NotificationCategory
        driver_for_notif = await db.get(Driver, payload.driver_id)
        if driver_for_notif and driver_for_notif.user_id:
            notification = Notification(
                category=NotificationCategory.TRIP,
                title="New Trip Assigned",
                description=f"Trip {trip.origin_location} to {trip.destination_location} has been assigned to you.",
                company_id=current_user.company_id,
                user_id=driver_for_notif.user_id,
            )
            db.add(notification)
            
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
    from services.eta_service import EtaService
    service = TripService(uow)
    trip = await service.get_trip(trip_id)
    if not trip or trip.company_id != current_user.company_id:
        raise HTTPException(404, f"Trip {trip_id} not found")
        
    trip_resp = TripResponse.model_validate(trip)
    if trip.status == TripStatus.IN_PROGRESS:
        eta_session = getattr(uow, "session", getattr(uow, "_session", None))
        if eta_session:
            try:
                eta_service = EtaService(eta_session)
                enrichment = await eta_service.enrich_trip_response(trip)
                trip_resp.estimated_arrival_time = enrichment.get("estimated_arrival_time")
            except Exception as e:
                pass
        
    return trip_resp


@router.patch("/trips/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: int,
    payload: TripUpdated,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TripResponse:
    from models.trip_domain import Trip, TripStatus
    from models.vehicle_domain import Vehicle, VehicleStatus
    from models.driver_domain import Driver, DriverStatus
    from services.trip_service import validate_state_transition, create_trip_operational_event
    from models.operational_event import EventType
    from sqlalchemy import select
    from datetime import datetime, timezone

    # Lock trip row for update to ensure concurrency safety
    stmt = select(Trip).where(Trip.id == trip_id, Trip.company_id == current_user.company_id).with_for_update()
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(404, f"Trip {trip_id} not found")

    # Terminal state protection
    if trip.status in (TripStatus.COMPLETED, TripStatus.CANCELLED):
        raise HTTPException(400, f"Cannot update a trip in terminal state '{trip.status.value}'")

    # State transition check
    if payload.status is not None and payload.status != trip.status:
        if not validate_state_transition(trip.status, payload.status):
            raise HTTPException(400, f"Invalid trip state transition from {trip.status.value} to {payload.status.value}")
        old_status = trip.status
        trip.status = payload.status
        if trip.status == TripStatus.IN_PROGRESS and not trip.actual_start_time:
            trip.actual_start_time = datetime.now(timezone.utc)
        elif trip.status == TripStatus.COMPLETED and not trip.actual_end_time:
            trip.actual_end_time = datetime.now(timezone.utc)

        # Emit corresponding event
        status_event_map = {
            TripStatus.IN_PROGRESS: EventType.TRIP_STARTED if old_status == TripStatus.CREATED else EventType.TRIP_RESUMED,
            TripStatus.PAUSED: EventType.TRIP_PAUSED,
            TripStatus.COMPLETED: EventType.TRIP_COMPLETED,
            TripStatus.CANCELLED: EventType.TRIP_CANCELLED,
        }
        event_type = status_event_map.get(payload.status)
        if event_type:
            event = create_trip_operational_event(
                company_id=current_user.company_id,
                event_type=event_type,
                trip_business_id=trip.trip_id,
                payload={"from_status": old_status.value, "to_status": payload.status.value},
                created_by=str(current_user.id)
            )
            db.add(event)

    # State checks for driver / vehicle reassignment while trip is active
    if payload.driver_id is not None and payload.driver_id != trip.driver_id:
        if trip.status in (TripStatus.IN_PROGRESS, TripStatus.PAUSED):
            raise HTTPException(400, "Cannot reassign driver while trip is active")

    if payload.vehicle_id is not None and payload.vehicle_id != trip.vehicle_id:
        if trip.status in (TripStatus.IN_PROGRESS, TripStatus.PAUSED):
            raise HTTPException(400, "Cannot reassign vehicle while trip is active")

    # Candidate values for assignment / cargo evaluation
    target_vehicle_id = payload.vehicle_id if payload.vehicle_id is not None else trip.vehicle_id
    target_driver_id = payload.driver_id if payload.driver_id is not None else trip.driver_id
    target_cargo_weight = payload.cargo_weight if payload.cargo_weight is not None else trip.cargo_weight
    target_cargo_category = payload.cargo_category if payload.cargo_category is not None else trip.cargo_category
    target_req_vc = payload.required_vehicle_class if payload.required_vehicle_class is not None else trip.required_vehicle_class
    target_req_dq = payload.required_driver_qualification if payload.required_driver_qualification is not None else trip.required_driver_qualification
    target_temp_req = payload.cargo_temperature_required if payload.cargo_temperature_required is not None else trip.cargo_temperature_required

    has_assignment_or_cargo_change = any([
        payload.vehicle_id is not None and payload.vehicle_id != trip.vehicle_id,
        payload.driver_id is not None and payload.driver_id != trip.driver_id,
        payload.cargo_weight is not None,
        payload.cargo_category is not None,
        payload.required_vehicle_class is not None,
        payload.required_driver_qualification is not None,
        payload.cargo_temperature_required is not None
    ])

    if has_assignment_or_cargo_change:
        from services.dispatch_suitability_service import DispatchSuitabilityService
        suitability_service = DispatchSuitabilityService(db)
        suit_res = await suitability_service.evaluate_dispatch_suitability(
            company_id=current_user.company_id,
            vehicle_id=target_vehicle_id,
            driver_id=target_driver_id,
            planned_start=trip.planned_start_time,
            planned_end=trip.planned_end_time,
            route_distance_km=trip.route_distance_km or trip.planned_distance,
            cargo_weight=target_cargo_weight,
            cargo_category=target_cargo_category,
            required_vehicle_class=target_req_vc,
            required_driver_qualification=target_req_dq,
            cargo_temperature_required=target_temp_req,
            exclude_trip_id=trip.id,
        )
        if suit_res.hard_failures:
            raise HTTPException(400, "; ".join(suit_res.hard_failures))

        if payload.cargo_weight is not None:
            trip.cargo_weight = payload.cargo_weight
        if payload.cargo_category is not None:
            trip.cargo_category = payload.cargo_category
        if payload.required_vehicle_class is not None:
            trip.required_vehicle_class = payload.required_vehicle_class
        if payload.required_driver_qualification is not None:
            trip.required_driver_qualification = payload.required_driver_qualification
        if payload.cargo_temperature_required is not None:
            trip.cargo_temperature_required = payload.cargo_temperature_required

    # Driver assignment / reassignment
    if payload.driver_id is not None and payload.driver_id != trip.driver_id:
        if trip.status in (TripStatus.IN_PROGRESS, TripStatus.PAUSED):
            raise HTTPException(400, "Cannot reassign driver while trip is active")

        driver = await db.get(Driver, payload.driver_id)
        if not driver or driver.company_id != current_user.company_id:
            raise HTTPException(400, "Invalid driver_id")
        if driver.status != DriverStatus.ACTIVE:
            raise HTTPException(400, f"Driver is not active (status is {driver.status.value})")

        stmt_d = select(Trip).where(
            Trip.driver_id == payload.driver_id,
            Trip.status.in_([TripStatus.IN_PROGRESS, TripStatus.PAUSED]),
            Trip.id != trip.id
        )
        if (await db.execute(stmt_d)).scalar_one_or_none():
            raise HTTPException(400, "Assigned driver already has an active trip in progress")

        trip.driver_id = payload.driver_id
        event = create_trip_operational_event(
            company_id=current_user.company_id,
            event_type=EventType.TRIP_DRIVER_ASSIGNED,
            trip_business_id=trip.trip_id,
            payload={"driver_id": payload.driver_id},
            created_by=str(current_user.id)
        )
        db.add(event)

    # Vehicle assignment / reassignment
    if payload.vehicle_id is not None and payload.vehicle_id != trip.vehicle_id:
        if trip.status in (TripStatus.IN_PROGRESS, TripStatus.PAUSED):
            raise HTTPException(400, "Cannot reassign vehicle while trip is active")

        vehicle = await db.get(Vehicle, payload.vehicle_id)
        if not vehicle or vehicle.company_id != current_user.company_id:
            raise HTTPException(400, "Invalid vehicle_id")
        if vehicle.status != VehicleStatus.ACTIVE:
            raise HTTPException(400, f"Vehicle is not eligible for dispatch (status is {vehicle.status.value})")

        stmt_v = select(Trip).where(
            Trip.vehicle_id == payload.vehicle_id,
            Trip.status.in_([TripStatus.IN_PROGRESS, TripStatus.PAUSED]),
            Trip.id != trip.id
        )
        if (await db.execute(stmt_v)).scalar_one_or_none():
            raise HTTPException(400, "Assigned vehicle already has an active trip in progress")

        trip.vehicle_id = payload.vehicle_id
        event = create_trip_operational_event(
            company_id=current_user.company_id,
            event_type=EventType.TRIP_VEHICLE_ASSIGNED,
            trip_business_id=trip.trip_id,
            payload={"vehicle_id": payload.vehicle_id},
            created_by=str(current_user.id)
        )
        db.add(event)

    await db.commit()
    await db.refresh(trip)
    return TripResponse.model_validate(trip)


@router.post("/trips/{trip_id}/cancel", response_model=TripResponse)
async def cancel_trip(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TripResponse:
    """
    Cancel an active or planned trip.
    Validates company ownership, state machine, releases resources,
    and records an authoritative TRIP_CANCELLED operational event.
    """
    from models.trip_domain import Trip, TripStatus
    from services.trip_service import create_trip_operational_event
    from models.operational_event import EventType
    from sqlalchemy import select

    stmt = select(Trip).where(Trip.id == trip_id, Trip.company_id == current_user.company_id).with_for_update()
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(404, f"Trip {trip_id} not found")

    if trip.status == TripStatus.COMPLETED:
        raise HTTPException(400, "Cannot cancel an already completed trip")

    if trip.status == TripStatus.CANCELLED:
        return TripResponse.model_validate(trip)

    trip.status = TripStatus.CANCELLED

    event = create_trip_operational_event(
        company_id=current_user.company_id,
        event_type=EventType.TRIP_CANCELLED,
        trip_business_id=trip.trip_id,
        payload={"reason": "Cancelled by dispatcher/admin"},
        created_by=str(current_user.id)
    )
    db.add(event)
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


@router.post("/trips/{trip_id}/retry-telemetry", response_model=TripResponse)
async def retry_trip_telemetry(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(requires_role(UserRole.COMPANY_ADMIN, UserRole.FLEET_MANAGER, UserRole.ADMIN, UserRole.DISPATCHER))
) -> TripResponse:
    """Manually trigger telemetry finalization for a completed trip.
    This is an idempotent operation that recalculates canonical GPS and fuel distances if missing.
    """
    from models.trip_domain import Trip
    from services.trip_completion_service import TripCompletionService
    
    trip = await db.get(Trip, trip_id)
    if not trip or trip.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    if trip.status != TripStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Only completed trips can have telemetry finalized.")
        
    svc = TripCompletionService(db)
    await svc.finalize_trip_telemetry(trip.id)
    await db.refresh(trip)
    
    return TripResponse.model_validate(trip)
