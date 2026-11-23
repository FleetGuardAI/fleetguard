"""
FleetGuard — Intelligent Route Optimization & Deviation API Router
Provides comprehensive endpoints for:
- Calculating route alternatives with vehicle restrictions & cost estimates
- Approving, persisting, and versioning routes
- Retrieving active approved routes and historical route versions
- Real-time route recalculation from driver's current position
- Driver obstruction and detour reporting
- Manager deviation incident inspection, acknowledgement, and resolution
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from models.trip_domain import Trip, TripStatus
from models.vehicle_domain import Vehicle
from models.driver_domain import Driver
from models.route_domain import (
    RouteVersion, RouteDeviationEvent, RouteVersionStatus, RouteType,
    DeviationStatus, DeviationSeverity, ObstructionReason
)
from services.auth_service import get_current_user
from routers.driver_mobile import get_current_driver
from services.routing.engine import RoutingEngine
from services.routing.schemas import (
    RouteCalculationInput, RouteCalculationOutput, RouteOption, CostEstimate
)
from services.route_version_service import RouteVersionService

logger = logging.getLogger("fleetguard.routing.api")

router = APIRouter(tags=["Route Intelligence"])


# ==========================================================================
# Schemas
# ==========================================================================

class RouteApprovalRequest(BaseModel):
    route_option_id: Optional[str] = None
    route_data: RouteOption
    selection_reason: Optional[str] = None


class RouteRecalculateRequest(BaseModel):
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    reason: Optional[str] = None


class DriverObstructionReport(BaseModel):
    reason_category: ObstructionReason
    notes: Optional[str] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None


class IncidentResolutionRequest(BaseModel):
    manager_notes: str
    resolution_status: str = "RESOLVED"  # RESOLVED or APPROVED_DETOUR


class RouteVersionResponse(BaseModel):
    id: int
    trip_id: int
    version_number: int
    route_type: str
    status: str
    origin_lat: float
    origin_lng: float
    origin_address: Optional[str] = None
    destination_lat: float
    destination_lng: float
    destination_address: Optional[str] = None
    polyline: str
    distance_km: float
    duration_hours: float
    duration_seconds: Optional[int] = None
    fuel_liters_estimate: Optional[float] = None
    fuel_cost_estimate: Optional[float] = None
    toll_cost_estimate: Optional[float] = None
    total_cost_estimate: Optional[float] = None
    currency: str
    vehicle_mileage_used: Optional[float] = None
    fuel_price_used: Optional[float] = None
    routing_provider: str
    selection_reason: Optional[str] = None
    reason_for_change: Optional[str] = None
    approved_by_user_id: Optional[int] = None
    approved_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DeviationEventResponse(BaseModel):
    id: int
    event_id: str
    trip_id: int
    status: str
    severity: str
    distance_from_route_meters: float
    max_distance_meters: float
    last_latitude: float
    last_longitude: float
    gps_accuracy: Optional[float] = None
    consecutive_outliers: int
    first_detected_at: datetime
    last_detected_at: datetime
    resolved_at: Optional[datetime] = None
    driver_explanation_category: Optional[str] = None
    driver_explanation_notes: Optional[str] = None
    driver_reported_at: Optional[datetime] = None
    manager_notes: Optional[str] = None
    acknowledged_by_user_id: Optional[int] = None
    acknowledged_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ==========================================================================
# Route Alternatives & Optimization Endpoints
# ==========================================================================

@router.post("/api/v1/trips/{trip_id}/routes/calculate", response_model=RouteCalculationOutput)
@router.post("/v1/trips/{trip_id}/routes/calculate", response_model=RouteCalculationOutput, include_in_schema=False)
async def calculate_trip_routes(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RouteCalculationOutput:
    """
    Calculates intelligent route alternatives for a trip.
    Considers vehicle fuel mileage, cargo weight, and road network restrictions.
    Returns 3 categorized alternatives: RECOMMENDED, FASTEST, LOWEST_COST.
    """
    trip = await db.get(Trip, trip_id)
    if not trip or trip.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Trip not found in your company fleet")

    if not trip.origin_lat or not trip.origin_lng or not trip.destination_lat or not trip.destination_lng:
        raise HTTPException(
            status_code=400,
            detail="Trip is missing origin or destination coordinates. Please update trip locations first."
        )

    # Fetch vehicle specifics if assigned
    vehicle_mileage = None
    vehicle_class = trip.required_vehicle_class
    if trip.vehicle_id:
        veh = await db.get(Vehicle, trip.vehicle_id)
        if veh:
            vehicle_mileage = getattr(veh, "mileage_empty", None) or getattr(veh, "mileage_loaded", None)
            if not vehicle_class:
                vehicle_class = getattr(veh, "vehicle_class", None)

    engine = RoutingEngine()
    req_input = RouteCalculationInput(
        origin_lat=trip.origin_lat,
        origin_lng=trip.origin_lng,
        destination_lat=trip.destination_lat,
        destination_lng=trip.destination_lng,
        origin_address=trip.origin_address or trip.origin_location,
        destination_address=trip.destination_address or trip.destination_location,
        vehicle_id=trip.vehicle_id,
        vehicle_class=vehicle_class,
        vehicle_mileage=vehicle_mileage,
    )

    try:
        output = await engine.calculate_routes(req_input)
        return output
    except Exception as e:
        logger.error(f"Error calculating routes for trip #{trip_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/trips/{trip_id}/routes/approve", response_model=RouteVersionResponse)
@router.post("/v1/trips/{trip_id}/routes/approve", response_model=RouteVersionResponse, include_in_schema=False)
async def approve_trip_route(
    trip_id: int,
    payload: RouteApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RouteVersionResponse:
    """
    Fleet owner or dispatcher approves a calculated route option.
    Persists RouteVersion with full geometry and cost estimates, updating Trip active route.
    """
    trip = await db.get(Trip, trip_id)
    if not trip or trip.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Trip not found")

    version_service = RouteVersionService(db)
    new_version = await version_service.persist_route_version(
        trip_id=trip.id,
        company_id=current_user.company_id,
        route_option_data=payload.route_data.model_dump(),
        status=RouteVersionStatus.APPROVED,
        approved_by_user_id=current_user.id,
        selection_reason=payload.selection_reason or payload.route_data.selection_reason,
    )

    # Broadcast updated route to Driver via WebSocket
    if trip.driver_id:
        try:
            from routers.ws_driver import ws_manager
            await ws_manager.send_personal_message({
                "type": "route_approved",
                "trip_id": trip.trip_id,
                "route_version": new_version.version_number,
                "distance_km": new_version.distance_km,
                "duration_hours": new_version.duration_hours,
                "polyline": new_version.polyline
            }, trip.driver_id)
        except Exception as e:
            logger.warning(f"Could not push route update to driver ws: {e}")

    return RouteVersionResponse.model_validate(new_version)


@router.get("/api/v1/trips/{trip_id}/routes/active", response_model=RouteVersionResponse)
@router.get("/v1/trips/{trip_id}/routes/active", response_model=RouteVersionResponse, include_in_schema=False)
async def get_active_route(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RouteVersionResponse:
    """Retrieves the active, approved route version for a trip."""
    trip = await db.get(Trip, trip_id)
    if not trip or trip.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Trip not found")

    version_service = RouteVersionService(db)
    active_version = await version_service.get_active_route_version(trip.id, current_user.company_id)
    if not active_version:
        # If no explicit RouteVersion was persisted yet, synthesize one from Trip columns if available
        if trip.route_polyline:
            return RouteVersionResponse(
                id=0,
                trip_id=trip.id,
                version_number=1,
                route_type="RECOMMENDED",
                status="APPROVED",
                origin_lat=trip.origin_lat or 0.0,
                origin_lng=trip.origin_lng or 0.0,
                origin_address=trip.origin_address or trip.origin_location,
                destination_lat=trip.destination_lat or 0.0,
                destination_lng=trip.destination_lng or 0.0,
                destination_address=trip.destination_address or trip.destination_location,
                polyline=trip.route_polyline,
                distance_km=trip.route_distance_km or 0.0,
                duration_hours=trip.route_duration_hours or 0.0,
                duration_seconds=int((trip.route_duration_hours or 0.0) * 3600),
                toll_cost_estimate=trip.route_toll_estimate,
                currency="INR",
                routing_provider=trip.route_provider or "google",
                created_at=datetime.now(timezone.utc)
            )
        raise HTTPException(status_code=404, detail="No approved route version found for this trip.")

    return RouteVersionResponse.model_validate(active_version)


@router.get("/api/v1/trips/{trip_id}/routes/versions", response_model=List[RouteVersionResponse])
@router.get("/v1/trips/{trip_id}/routes/versions", response_model=List[RouteVersionResponse], include_in_schema=False)
async def get_route_versions(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[RouteVersionResponse]:
    """Retrieves the complete route version history for auditing."""
    trip = await db.get(Trip, trip_id)
    if not trip or trip.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Trip not found")

    version_service = RouteVersionService(db)
    versions = await version_service.get_route_versions_for_trip(trip.id, current_user.company_id)
    return [RouteVersionResponse.model_validate(v) for v in versions]


# ==========================================================================
# Real-Time Route Recalculation & Approval
# ==========================================================================

@router.post("/api/v1/trips/{trip_id}/routes/recalculate", response_model=RouteCalculationOutput)
@router.post("/v1/trips/{trip_id}/routes/recalculate", response_model=RouteCalculationOutput, include_in_schema=False)
async def recalculate_route_from_current_position(
    trip_id: int,
    payload: RouteRecalculateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RouteCalculationOutput:
    """
    Recalculates route alternatives from driver's current coordinates to trip destination.
    Used during confirmed deviations or road obstructions.
    """
    trip = await db.get(Trip, trip_id)
    if not trip or trip.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Trip not found")

    origin_lat = payload.current_lat
    origin_lng = payload.current_lng

    # If coordinates not provided in payload, look up driver's last known position
    if not origin_lat or not origin_lng:
        if trip.driver_id:
            driver = await db.get(Driver, trip.driver_id)
            if driver and driver.last_known_lat and driver.last_known_lng:
                origin_lat = driver.last_known_lat
                origin_lng = driver.last_known_lng

    if not origin_lat or not origin_lng:
        raise HTTPException(
            status_code=400,
            detail="Driver's current GPS position is unavailable for route recalculation."
        )

    engine = RoutingEngine()
    req_input = RouteCalculationInput(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        destination_lat=trip.destination_lat,
        destination_lng=trip.destination_lng,
        origin_address="Current Driver Location",
        destination_address=trip.destination_address or trip.destination_location,
        vehicle_id=trip.vehicle_id,
        vehicle_class=trip.required_vehicle_class,
    )

    output = await engine.calculate_routes(req_input)
    return output


# ==========================================================================
# Driver Obstruction Reporting (Driver App Endpoint)
# ==========================================================================

@router.post("/api/v1/driver-app/trips/{trip_id}/deviation-explanation")
@router.post("/v1/driver-app/trips/{trip_id}/deviation-explanation", include_in_schema=False)
async def report_deviation_explanation(
    trip_id: int,
    payload: DriverObstructionReport,
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Allows driver to report a legitimate road obstruction or operational deviation reason.
    Associates explanation with the active deviation incident and notifies the fleet owner.
    """
    trip = await db.get(Trip, trip_id)
    if not trip or trip.driver_id != driver.id or trip.company_id != driver.company_id:
        raise HTTPException(status_code=404, detail="Trip not found for authenticated driver")

    now = datetime.now(timezone.utc)

    # Find the most recent active deviation event
    stmt = (
        select(RouteDeviationEvent)
        .where(
            RouteDeviationEvent.trip_id == trip.id,
            RouteDeviationEvent.company_id == driver.company_id,
            RouteDeviationEvent.status.in_([
                DeviationStatus.SUSPECTED,
                DeviationStatus.CONFIRMED,
                DeviationStatus.OBSTRUCTION_REPORTED
            ])
        )
        .order_by(desc(RouteDeviationEvent.id))
        .limit(1)
    )
    res = await db.execute(stmt)
    event = res.scalar_one_or_none()

    if not event:
        # Create an event representing driver-reported detour
        import uuid
        event = RouteDeviationEvent(
            event_id=f"DEV-{str(uuid.uuid4())[:8].upper()}",
            trip_id=trip.id,
            company_id=driver.company_id,
            driver_id=driver.id,
            vehicle_id=trip.vehicle_id,
            route_version_id=trip.approved_route_version_id,
            status=DeviationStatus.OBSTRUCTION_REPORTED,
            severity=DeviationSeverity.MEDIUM,
            distance_from_route_meters=0.0,
            max_distance_meters=0.0,
            last_latitude=payload.current_lat or driver.last_known_lat or trip.origin_lat or 0.0,
            last_longitude=payload.current_lng or driver.last_known_lng or trip.origin_lng or 0.0,
            first_detected_at=now,
            last_detected_at=now,
            driver_explanation_category=payload.reason_category,
            driver_explanation_notes=payload.notes,
            driver_reported_at=now
        )
        db.add(event)
    else:
        event.status = DeviationStatus.OBSTRUCTION_REPORTED
        event.driver_explanation_category = payload.reason_category
        event.driver_explanation_notes = payload.notes
        event.driver_reported_at = now

    await db.commit()
    await db.refresh(event)

    # Notify Fleet Manager
    notif = Notification(
        category=NotificationCategory.ALERT,
        title="Driver Reported Road Obstruction",
        description=f"Driver {driver.name} reported {payload.reason_category.value} on trip {trip.trip_id}: {payload.notes or 'No additional notes'}",
        company_id=driver.company_id,
        user_id=None,
    )
    db.add(notif)
    await db.commit()

    # WebSocket Broadcast
    try:
        from routers.ws_driver import owner_ws_manager
        await owner_ws_manager.broadcast_to_company(driver.company_id, {
            "type": "obstruction_reported",
            "event_id": event.event_id,
            "trip_id": trip.trip_id,
            "driver_name": driver.name,
            "reason": payload.reason_category.value,
            "notes": payload.notes,
            "reported_at": now.isoformat()
        })
    except Exception as e:
        logger.warning(f"WebSocket obstruction broadcast error: {e}")

    return {
        "message": "Obstruction report recorded successfully",
        "event_id": event.event_id,
        "status": event.status.value
    }


# ==========================================================================
# Deviation Incident Inspection & Acknowledgement Endpoints (Owner App)
# ==========================================================================

@router.get("/api/v1/trips/{trip_id}/deviations", response_model=List[DeviationEventResponse])
@router.get("/v1/trips/{trip_id}/deviations", response_model=List[DeviationEventResponse], include_in_schema=False)
async def get_trip_deviations(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[DeviationEventResponse]:
    """Retrieves all deviation incidents associated with a trip."""
    trip = await db.get(Trip, trip_id)
    if not trip or trip.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Trip not found in your company fleet")

    stmt = (
        select(RouteDeviationEvent)
        .where(
            RouteDeviationEvent.trip_id == trip.id,
            RouteDeviationEvent.company_id == current_user.company_id
        )
        .order_by(desc(RouteDeviationEvent.first_detected_at))
    )
    res = await db.execute(stmt)
    events = res.scalars().all()
    return [DeviationEventResponse.model_validate(e) for e in events]


@router.post("/api/v1/trips/{trip_id}/deviations/{event_id}/acknowledge")
@router.post("/v1/trips/{trip_id}/deviations/{event_id}/acknowledge", include_in_schema=False)
async def acknowledge_deviation_event(
    trip_id: int,
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fleet manager acknowledges a confirmed route deviation incident."""
    stmt = select(RouteDeviationEvent).where(
        RouteDeviationEvent.event_id == event_id,
        RouteDeviationEvent.trip_id == trip_id,
        RouteDeviationEvent.company_id == current_user.company_id
    )
    res = await db.execute(stmt)
    event = res.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Deviation incident not found")

    event.acknowledged_by_user_id = current_user.id
    event.acknowledged_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "message": "Incident acknowledged",
        "event_id": event.event_id,
        "acknowledged_at": event.acknowledged_at.isoformat()
    }


@router.post("/api/v1/trips/{trip_id}/deviations/{event_id}/resolve")
@router.post("/v1/trips/{trip_id}/deviations/{event_id}/resolve", include_in_schema=False)
async def resolve_deviation_event(
    trip_id: int,
    event_id: str,
    payload: IncidentResolutionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fleet manager resolves or approves detour for a deviation incident."""
    stmt = select(RouteDeviationEvent).where(
        RouteDeviationEvent.event_id == event_id,
        RouteDeviationEvent.trip_id == trip_id,
        RouteDeviationEvent.company_id == current_user.company_id
    )
    res = await db.execute(stmt)
    event = res.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Deviation incident not found")

    now = datetime.now(timezone.utc)
    event.manager_notes = payload.manager_notes
    if payload.resolution_status == "APPROVED_DETOUR":
        event.status = DeviationStatus.APPROVED_DETOUR
    else:
        event.status = DeviationStatus.RESOLVED

    event.resolved_at = now
    if not event.acknowledged_at:
        event.acknowledged_at = now
        event.acknowledged_by_user_id = current_user.id

    await db.commit()
    return {
        "message": "Incident resolved",
        "event_id": event.event_id,
        "status": event.status.value,
        "resolved_at": event.resolved_at.isoformat()
    }
