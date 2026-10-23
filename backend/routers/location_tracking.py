"""
FleetGuard — Location Tracking & GPS Historical Playback API Router

Provides production-ready, company-scoped endpoints for:
- Driver location ingestion & live telemetry broadcast
- Driver list enriched with vehicle assignment, trip count & GPS freshness
- Driver trip history with GPS point counts & date filtering
- High-precision chronological historical GPS points with gaps & stops
- Deterministic operational analytics (distance, speeds, durations, gaps)
- Trip-specific route retrieval (by ID or business identifier)
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, func, desc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from routers.driver_mobile import get_current_driver

from database import get_db
from models.driver_domain import Driver, DutyStatus
from models.location_tracking import DriverLocation, LocationSource
from models.trip_domain import Trip, TripStatus
from models.vehicle_domain import Vehicle
from models.user import User
from services.auth_service import get_current_user
from utils.geo_analytics import (
    haversine_distance_meters,
    detect_gaps_and_stops,
    compute_bounding_box,
    downsample_gps_points,
    calculate_comprehensive_analytics,
)

logger = logging.getLogger("fleetguard.tracking")

router = APIRouter(tags=["Location Tracking"])


# ==========================================================================
# Pydantic Schemas
# ==========================================================================

class LocationPoint(BaseModel):
    latitude: float
    longitude: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None
    timestamp: str
    battery_percent: Optional[int] = None
    activity_state: Optional[str] = None


class LocationBatchRequest(BaseModel):
    driver_id: Optional[int] = None
    locations: List[LocationPoint]


class LocationResponse(BaseModel):
    id: int
    driver_id: int
    latitude: float
    longitude: float
    speed: Optional[float] = None
    speed_kmh: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None
    timestamp: datetime
    battery_percent: Optional[int] = None
    activity_state: Optional[str] = None
    source: str = "driver_app"
    trip_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LiveDriverLocation(BaseModel):
    driver_id: int
    driver_name: str
    latitude: float
    longitude: float
    speed: Optional[float] = None
    speed_kmh: Optional[float] = None
    heading: Optional[float] = None
    battery_percent: Optional[int] = None
    duty_status: Optional[str] = None
    last_updated: Optional[datetime] = None
    vehicle_id: Optional[int] = None
    vehicle_registration: Optional[str] = None
    trip_id: Optional[str] = None


class DriverLatestTrip(BaseModel):
    id: int
    trip_id: str
    status: str
    origin_location: Optional[str] = None
    destination_location: Optional[str] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None


class DriverSummaryResponse(BaseModel):
    id: int
    name: str
    phone_number: str
    avatar_url: Optional[str] = None
    employee_id: Optional[str] = None
    status: str
    duty_status: Optional[str] = None
    last_known_lat: Optional[float] = None
    last_known_lng: Optional[float] = None
    last_location_at: Optional[datetime] = None
    vehicle_id: Optional[int] = None
    vehicle_registration: Optional[str] = None
    vehicle_make: Optional[str] = None
    vehicle_model: Optional[str] = None
    total_trips: int = 0
    latest_trip: Optional[DriverLatestTrip] = None
    gps_point_count: int = 0


class DriverTripSummary(BaseModel):
    id: int
    trip_id: str
    status: str
    origin_location: Optional[str] = None
    destination_location: Optional[str] = None
    planned_start_time: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    planned_end_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    route_distance_km: Optional[float] = None
    actual_distance: Optional[float] = None
    vehicle_id: Optional[int] = None
    vehicle_registration: Optional[str] = None
    gps_point_count: int = 0
    has_gps_data: bool = False


class DetailedLocationPoint(BaseModel):
    id: int
    driver_id: int
    latitude: float
    longitude: float
    speed_mps: Optional[float] = None
    speed_kmh: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None
    timestamp: datetime
    server_receipt_timestamp: datetime
    battery_percent: Optional[int] = None
    activity_state: Optional[str] = None
    source: str
    trip_id: Optional[str] = None


class PaginatedLocationResponse(BaseModel):
    driver_id: int
    driver_name: str
    time_range: Dict[str, Optional[str]]
    trip_id: Optional[str] = None
    total_points: int
    returned_points: int
    page: int
    page_size: int
    total_pages: int
    has_more: bool
    is_downsampled: bool
    bounds: Optional[List[float]] = None
    points: List[DetailedLocationPoint]
    gaps: List[Dict[str, Any]]
    stops: List[Dict[str, Any]]


class DriverTrackingAnalytics(BaseModel):
    driver_id: int
    driver_name: str
    time_range: Dict[str, Optional[str]]
    trip_id: Optional[str] = None
    total_trips: int
    total_recorded_distance_km: Optional[float] = None
    total_duration_seconds: Optional[float] = None
    moving_duration_seconds: Optional[float] = None
    stationary_duration_seconds: Optional[float] = None
    average_speed_kmh: Optional[float] = None
    max_speed_kmh: Optional[float] = None
    valid_speed_samples: int = 0
    gps_coverage_pct: Optional[float] = None
    gps_gap_count: int = 0
    total_points_analyzed: int = 0
    first_recorded_point: Optional[Dict[str, Any]] = None
    last_recorded_point: Optional[Dict[str, Any]] = None
    last_known_location: Optional[Dict[str, Any]] = None


# ==========================================================================
# Driver App Telemetry Ingestion
# ==========================================================================

@router.post("/api/v1/driver-app/location/batch", status_code=201)
async def batch_upload_locations(
    payload: LocationBatchRequest,
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Batch upload GPS locations from driver's phone.
    Accepts queued offline locations for sync.
    Associates with active IN_PROGRESS trip if one is running.
    """
    if driver is None:
        raise HTTPException(404, "Driver not found")

    # Check for active trip
    active_trip_res = await db.execute(
        select(Trip.trip_id).where(
            Trip.driver_id == driver.id,
            Trip.status == TripStatus.IN_PROGRESS
        ).limit(1)
    )
    current_trip_id = active_trip_res.scalar_one_or_none()

    locations_added = 0
    latest_location = None

    for loc in payload.locations:
        try:
            ts = datetime.fromisoformat(loc.timestamp.replace("Z", "+00:00"))
        except ValueError:
            ts = datetime.now(tz=timezone.utc)

        db_loc = DriverLocation(
            driver_id=driver.id,
            company_id=driver.company_id or 0,
            latitude=loc.latitude,
            longitude=loc.longitude,
            speed=loc.speed,
            heading=loc.heading,
            accuracy=loc.accuracy,
            timestamp=ts,
            battery_percent=loc.battery_percent,
            activity_state=loc.activity_state,
            source=LocationSource.PHONE_GPS,
            trip_id=current_trip_id,
        )
        db.add(db_loc)
        locations_added += 1
        latest_location = loc

    # Update driver's last known position
    if latest_location:
        driver.last_known_lat = latest_location.latitude
        driver.last_known_lng = latest_location.longitude
        driver.last_location_at = datetime.now(tz=timezone.utc)

    await db.commit()

    if latest_location:
        from routers.ws_driver import owner_ws_manager
        await owner_ws_manager.broadcast_to_company(driver.company_id or 0, {
            "type": "location_update",
            "driver_id": driver.id,
            "driver_name": driver.name,
            "latitude": latest_location.latitude,
            "longitude": latest_location.longitude,
            "speed": latest_location.speed,
            "heading": latest_location.heading,
            "battery_percent": latest_location.battery_percent,
            "duty_status": driver.duty_status.value if driver.duty_status else None,
            "last_updated": datetime.now(tz=timezone.utc).isoformat()
        })

    logger.info(f"Driver {driver.id}: {locations_added} locations synced")
    return {"message": f"{locations_added} locations recorded"}


# ==========================================================================
# Fleet Owner Trip History & GPS Tracking Endpoints
# ==========================================================================

@router.get("/api/v1/tracking/drivers", response_model=List[DriverSummaryResponse])
async def list_tracking_drivers(
    search: Optional[str] = Query(None, description="Search by name, phone, employee ID, or vehicle registration"),
    duty_status: Optional[str] = Query(None, description="Filter by duty status: ON_DUTY, OFF_DUTY, ON_BREAK"),
    has_trips: Optional[bool] = Query(None, description="Filter drivers with trip history"),
    sort_by: str = Query("latest_activity", description="Sort by: name, latest_activity, trips_count, gps_points"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all drivers for the authenticated fleet owner's company, enriched with:
    - Assigned vehicle details (registration plate, make, model)
    - Real-time/historical duty status and last GPS timestamp
    - Total completed and active trips count
    - Most recent trip metadata
    - Total recorded GPS points count
    Enforces strict tenant isolation.
    """
    company_id = current_user.company_id

    # Base query for drivers
    query = (
        select(Driver, Vehicle)
        .outerjoin(Vehicle, Vehicle.assigned_driver_id == Driver.id)
        .where(Driver.company_id == company_id)
    )

    if duty_status:
        try:
            ds_enum = DutyStatus(duty_status.upper())
            query = query.where(Driver.duty_status == ds_enum)
        except ValueError:
            pass

    if search:
        search_term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Driver.name.ilike(search_term),
                Driver.phone_number.ilike(search_term),
                Driver.employee_id.ilike(search_term),
                Vehicle.registration_number.ilike(search_term),
            )
        )

    # Fetch drivers and vehicles
    result = await db.execute(query)
    driver_vehicle_rows = result.all()

    if not driver_vehicle_rows:
        return []

    driver_ids = [d.id for d, _ in driver_vehicle_rows]

    # Batch query trip counts per driver
    trip_counts_query = (
        select(Trip.driver_id, func.count(Trip.id).label("trip_count"))
        .where(Trip.company_id == company_id, Trip.driver_id.in_(driver_ids))
        .group_by(Trip.driver_id)
    )
    trip_counts_res = await db.execute(trip_counts_query)
    trip_counts_map = dict(trip_counts_res.all())

    # Batch query GPS point counts per driver
    gps_counts_query = (
        select(DriverLocation.driver_id, func.count(DriverLocation.id).label("gps_count"))
        .where(DriverLocation.company_id == company_id, DriverLocation.driver_id.in_(driver_ids))
        .group_by(DriverLocation.driver_id)
    )
    gps_counts_res = await db.execute(gps_counts_query)
    gps_counts_map = dict(gps_counts_res.all())

    # Batch query most recent trip for each driver
    latest_trips_query = (
        select(Trip)
        .where(Trip.company_id == company_id, Trip.driver_id.in_(driver_ids))
        .order_by(Trip.actual_start_time.desc().nullslast(), Trip.id.desc())
    )
    latest_trips_res = await db.execute(latest_trips_query)
    latest_trips = latest_trips_res.scalars().all()
    latest_trips_map: Dict[int, Trip] = {}
    for t in latest_trips:
        if t.driver_id not in latest_trips_map:
            latest_trips_map[t.driver_id] = t

    # Build response list
    drivers_list: List[DriverSummaryResponse] = []
    for d, v in driver_vehicle_rows:
        t_count = trip_counts_map.get(d.id, 0)
        gps_count = gps_counts_map.get(d.id, 0)

        if has_trips is True and t_count == 0:
            continue
        if has_trips is False and t_count > 0:
            continue

        l_trip = latest_trips_map.get(d.id)
        latest_trip_obj = None
        if l_trip:
            latest_trip_obj = DriverLatestTrip(
                id=l_trip.id,
                trip_id=l_trip.trip_id,
                status=l_trip.status.value if l_trip.status else "UNKNOWN",
                origin_location=l_trip.origin_location,
                destination_location=l_trip.destination_location,
                actual_start_time=l_trip.actual_start_time,
                actual_end_time=l_trip.actual_end_time,
            )

        resp = DriverSummaryResponse(
            id=d.id,
            name=d.name,
            phone_number=d.phone_number,
            avatar_url=d.avatar_url,
            employee_id=d.employee_id,
            status=d.status.value if d.status else "ACTIVE",
            duty_status=d.duty_status.value if d.duty_status else None,
            last_known_lat=d.last_known_lat,
            last_known_lng=d.last_known_lng,
            last_location_at=d.last_location_at,
            vehicle_id=v.id if v else None,
            vehicle_registration=v.registration_number if v else None,
            vehicle_make=v.make if v else None,
            vehicle_model=v.model if v else None,
            total_trips=t_count,
            latest_trip=latest_trip_obj,
            gps_point_count=gps_count,
        )
        drivers_list.append(resp)

    # Sort
    if sort_by == "name":
        drivers_list.sort(key=lambda x: x.name.lower())
    elif sort_by == "trips_count":
        drivers_list.sort(key=lambda x: x.total_trips, reverse=True)
    elif sort_by == "gps_points":
        drivers_list.sort(key=lambda x: x.gps_point_count, reverse=True)
    else:  # latest_activity
        # Priority: drivers with recent location or recent trips
        def get_activity_key(item: DriverSummaryResponse):
            loc_time = item.last_location_at or datetime.min.replace(tzinfo=timezone.utc)
            trip_time = (
                item.latest_trip.actual_start_time or datetime.min.replace(tzinfo=timezone.utc)
                if item.latest_trip else datetime.min.replace(tzinfo=timezone.utc)
            )
            return max(loc_time, trip_time)
        drivers_list.sort(key=get_activity_key, reverse=True)

    # Paginate in memory
    return drivers_list[offset: offset + limit]


@router.get("/api/v1/tracking/driver/{driver_id}/trips", response_model=List[DriverTripSummary])
async def list_driver_trips(
    driver_id: int,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch all trips for a specific driver with GPS point counts and vehicle assignments.
    Enforces tenant isolation: driver must belong to current_user's company.
    """
    driver = await db.get(Driver, driver_id)
    if driver is None or driver.company_id != current_user.company_id:
        raise HTTPException(404, "Driver not found in your fleet")

    query = (
        select(Trip, Vehicle)
        .outerjoin(Vehicle, Vehicle.id == Trip.vehicle_id)
        .where(
            Trip.driver_id == driver_id,
            Trip.company_id == current_user.company_id,
        )
    )

    if status and status.upper() != "ALL":
        try:
            status_enum = TripStatus(status.upper())
            query = query.where(Trip.status == status_enum)
        except ValueError:
            pass

    if start_time:
        query = query.where(
            or_(
                Trip.actual_start_time >= start_time,
                Trip.planned_start_time >= start_time
            )
        )
    if end_time:
        query = query.where(
            or_(
                Trip.actual_end_time <= end_time,
                Trip.planned_end_time <= end_time,
                Trip.actual_start_time <= end_time
            )
        )

    query = query.order_by(
        Trip.actual_start_time.desc().nullslast(),
        Trip.id.desc()
    ).limit(limit).offset(offset)

    result = await db.execute(query)
    rows = result.all()

    trips_response: List[DriverTripSummary] = []
    for trip, veh in rows:
        # Determine GPS point count for this trip
        # Check by trip_id directly OR by time-window if trip_id column not set
        t_start = trip.actual_start_time or trip.planned_start_time
        t_end = trip.actual_end_time or datetime.now(timezone.utc)

        conditions = [DriverLocation.trip_id == trip.trip_id]
        if t_start:
            conditions.append(
                and_(
                    DriverLocation.driver_id == driver_id,
                    DriverLocation.timestamp >= t_start,
                    DriverLocation.timestamp <= t_end
                )
            )

        gps_count_res = await db.execute(
            select(func.count(DriverLocation.id)).where(
                DriverLocation.company_id == current_user.company_id,
                or_(*conditions)
            )
        )
        point_count = gps_count_res.scalar_one() or 0

        trips_response.append(DriverTripSummary(
            id=trip.id,
            trip_id=trip.trip_id,
            status=trip.status.value if trip.status else "UNKNOWN",
            origin_location=trip.origin_location,
            destination_location=trip.destination_location,
            planned_start_time=trip.planned_start_time,
            actual_start_time=trip.actual_start_time,
            planned_end_time=trip.planned_end_time,
            actual_end_time=trip.actual_end_time,
            route_distance_km=trip.route_distance_km,
            actual_distance=trip.actual_distance,
            vehicle_id=veh.id if veh else trip.vehicle_id,
            vehicle_registration=veh.registration_number if veh else None,
            gps_point_count=point_count,
            has_gps_data=point_count > 0,
        ))

    return trips_response


@router.get("/api/v1/tracking/driver/{driver_id}/locations", response_model=PaginatedLocationResponse)
async def get_driver_locations_paginated(
    driver_id: int,
    start_time: Optional[datetime] = Query(None, description="Start time (UTC)"),
    end_time: Optional[datetime] = Query(None, description="End time (UTC)"),
    trip_id: Optional[str] = Query(None, description="Trip ID or business identifier"),
    page: int = Query(1, ge=1),
    page_size: int = Query(2000, ge=10, le=5000),
    downsample_max: Optional[int] = Query(None, ge=50, le=2000, description="Max points to return for map rendering"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve chronological historical GPS points for a selected driver and time window.
    Features:
    - Chronological ascending sort (first point to last point)
    - Automatically bounds start_time and end_time if a trip_id is specified
    - Detects GPS signal gaps and prolonged stationary periods
    - Computes bounding box for immediate map fitting
    - Optional smart route downsampling for optimal rendering of dense datasets
    - Company-scoped tenant boundary protection
    """
    driver = await db.get(Driver, driver_id)
    if driver is None or driver.company_id != current_user.company_id:
        raise HTTPException(404, "Driver not found in your fleet")

    # If trip_id is provided, resolve the trip
    selected_trip = None
    if trip_id:
        # Check by numeric ID or business string
        trip_query = select(Trip).where(Trip.company_id == current_user.company_id)
        if trip_id.isdigit():
            trip_query = trip_query.where(or_(Trip.id == int(trip_id), Trip.trip_id == trip_id))
        else:
            trip_query = trip_query.where(Trip.trip_id == trip_id)

        t_res = await db.execute(trip_query)
        selected_trip = t_res.scalar_one_or_none()
        if not selected_trip:
            raise HTTPException(404, f"Trip {trip_id} not found in your company")

        if not start_time:
            start_time = selected_trip.actual_start_time or selected_trip.planned_start_time
        if not end_time and selected_trip.actual_end_time:
            end_time = selected_trip.actual_end_time

    # Build SQL filter for driver_locations
    conditions = [
        DriverLocation.driver_id == driver_id,
        DriverLocation.company_id == current_user.company_id,
        DriverLocation.latitude >= -90.0,
        DriverLocation.latitude <= 90.0,
        DriverLocation.longitude >= -180.0,
        DriverLocation.longitude <= 180.0,
    ]

    if selected_trip:
        trip_conditions = [DriverLocation.trip_id == selected_trip.trip_id]
        if start_time:
            time_filter = DriverLocation.timestamp >= start_time
            if end_time:
                time_filter = and_(DriverLocation.timestamp >= start_time, DriverLocation.timestamp <= end_time)
            trip_conditions.append(time_filter)
        conditions.append(or_(*trip_conditions))
    else:
        if start_time:
            conditions.append(DriverLocation.timestamp >= start_time)
        if end_time:
            conditions.append(DriverLocation.timestamp <= end_time)

    # Count total matching points in database
    count_stmt = select(func.count(DriverLocation.id)).where(and_(*conditions))
    total_count_res = await db.execute(count_stmt)
    total_points = total_count_res.scalar_one() or 0

    if total_points == 0:
        return PaginatedLocationResponse(
            driver_id=driver.id,
            driver_name=driver.name,
            time_range={
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
            },
            trip_id=selected_trip.trip_id if selected_trip else None,
            total_points=0,
            returned_points=0,
            page=page,
            page_size=page_size,
            total_pages=0,
            has_more=False,
            is_downsampled=False,
            bounds=None,
            points=[],
            gaps=[],
            stops=[],
        )

    # Query chronological points with pagination
    offset = (page - 1) * page_size
    query = (
        select(DriverLocation)
        .where(and_(*conditions))
        .order_by(DriverLocation.timestamp.asc(), DriverLocation.id.asc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(query)
    raw_points = result.scalars().all()

    # Convert to dictionary format for analytics & processing
    processed_dicts = []
    for p in raw_points:
        spd_mps = p.speed
        spd_kmh = round(spd_mps * 3.6, 1) if spd_mps is not None else None
        processed_dicts.append({
            "id": p.id,
            "driver_id": p.driver_id,
            "latitude": p.latitude,
            "longitude": p.longitude,
            "speed": spd_mps,
            "speed_mps": spd_mps,
            "speed_kmh": spd_kmh,
            "heading": p.heading,
            "accuracy": p.accuracy,
            "timestamp": p.timestamp,
            "server_receipt_timestamp": p.created_at,
            "battery_percent": p.battery_percent,
            "activity_state": p.activity_state,
            "source": p.source.value if hasattr(p.source, "value") else str(p.source),
            "trip_id": p.trip_id,
        })

    # Detect gaps and stops on the raw chronological slice
    gaps, stops = detect_gaps_and_stops(processed_dicts)
    bounds = compute_bounding_box(processed_dicts)

    is_downsampled = False
    final_points_data = processed_dicts

    if downsample_max and len(processed_dicts) > downsample_max:
        final_points_data = downsample_gps_points(processed_dicts, max_points=downsample_max)
        is_downsampled = True

    detailed_points = [
        DetailedLocationPoint(
            id=d["id"],
            driver_id=d["driver_id"],
            latitude=d["latitude"],
            longitude=d["longitude"],
            speed_mps=d["speed_mps"],
            speed_kmh=d["speed_kmh"],
            heading=d["heading"],
            accuracy=d["accuracy"],
            timestamp=d["timestamp"],
            server_receipt_timestamp=d["server_receipt_timestamp"],
            battery_percent=d["battery_percent"],
            activity_state=d["activity_state"],
            source=d["source"],
            trip_id=d["trip_id"],
        )
        for d in final_points_data
    ]

    total_pages = (total_points + page_size - 1) // page_size

    return PaginatedLocationResponse(
        driver_id=driver.id,
        driver_name=driver.name,
        time_range={
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
        },
        trip_id=selected_trip.trip_id if selected_trip else None,
        total_points=total_points,
        returned_points=len(detailed_points),
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_more=page < total_pages,
        is_downsampled=is_downsampled,
        bounds=bounds,
        points=detailed_points,
        gaps=gaps,
        stops=stops,
    )


@router.get("/api/v1/tracking/driver/{driver_id}/analytics", response_model=DriverTrackingAnalytics)
async def get_driver_tracking_analytics(
    driver_id: int,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    trip_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compute rigorous operational and geospatial analytics for a driver's GPS track:
    - Total recorded driving distance (haversine sum without telemetry jumps)
    - Total duration, moving time vs stationary time
    - Average and maximum recorded speeds
    - Data coverage percentage and GPS signal gaps count
    - First and last recorded position
    """
    driver = await db.get(Driver, driver_id)
    if driver is None or driver.company_id != current_user.company_id:
        raise HTTPException(404, "Driver not found in your fleet")

    selected_trip = None
    if trip_id:
        trip_query = select(Trip).where(Trip.company_id == current_user.company_id)
        if trip_id.isdigit():
            trip_query = trip_query.where(or_(Trip.id == int(trip_id), Trip.trip_id == trip_id))
        else:
            trip_query = trip_query.where(Trip.trip_id == trip_id)

        t_res = await db.execute(trip_query)
        selected_trip = t_res.scalar_one_or_none()
        if not selected_trip:
            raise HTTPException(404, f"Trip {trip_id} not found in your company")

        if not start_time:
            start_time = selected_trip.actual_start_time or selected_trip.planned_start_time
        if not end_time and selected_trip.actual_end_time:
            end_time = selected_trip.actual_end_time

    # Fetch total trips count in this time range
    trip_count_query = select(func.count(Trip.id)).where(
        Trip.company_id == current_user.company_id,
        Trip.driver_id == driver_id
    )
    if start_time:
        trip_count_query = trip_count_query.where(Trip.actual_start_time >= start_time)
    if end_time:
        trip_count_query = trip_count_query.where(Trip.actual_start_time <= end_time)
    trips_count_res = await db.execute(trip_count_query)
    total_trips_count = trips_count_res.scalar_one() or 0

    # Query chronological points (up to 5000 points for analytics)
    conditions = [
        DriverLocation.driver_id == driver_id,
        DriverLocation.company_id == current_user.company_id,
        DriverLocation.latitude >= -90.0,
        DriverLocation.latitude <= 90.0,
        DriverLocation.longitude >= -180.0,
        DriverLocation.longitude <= 180.0,
    ]
    if selected_trip:
        trip_conditions = [DriverLocation.trip_id == selected_trip.trip_id]
        if start_time:
            time_filter = DriverLocation.timestamp >= start_time
            if end_time:
                time_filter = and_(DriverLocation.timestamp >= start_time, DriverLocation.timestamp <= end_time)
            trip_conditions.append(time_filter)
        conditions.append(or_(*trip_conditions))
    else:
        if start_time:
            conditions.append(DriverLocation.timestamp >= start_time)
        if end_time:
            conditions.append(DriverLocation.timestamp <= end_time)

    query = (
        select(DriverLocation)
        .where(and_(*conditions))
        .order_by(DriverLocation.timestamp.asc())
        .limit(5000)
    )
    result = await db.execute(query)
    raw_points = result.scalars().all()

    points_dicts = [
        {
            "id": p.id,
            "latitude": p.latitude,
            "longitude": p.longitude,
            "speed": p.speed,
            "speed_kmh": round(p.speed * 3.6, 1) if p.speed is not None else None,
            "heading": p.heading,
            "timestamp": p.timestamp,
        }
        for p in raw_points
    ]

    metrics = calculate_comprehensive_analytics(points_dicts, total_trips=total_trips_count)

    # Attach driver's last known location from Driver profile if points empty
    if not metrics.get("last_known_location") and driver.last_known_lat:
        metrics["last_known_location"] = {
            "latitude": driver.last_known_lat,
            "longitude": driver.last_known_lng,
            "timestamp": driver.last_location_at.isoformat() if driver.last_location_at else None,
            "speed_kmh": 0.0,
            "heading": 0.0,
        }

    return DriverTrackingAnalytics(
        driver_id=driver.id,
        driver_name=driver.name,
        time_range={
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
        },
        trip_id=selected_trip.trip_id if selected_trip else None,
        **metrics
    )


# ==========================================================================
# Legacy & Backwards Compatible Endpoints
# ==========================================================================

@router.get("/api/v1/tracking/driver/{driver_id}/live", response_model=LiveDriverLocation)
async def get_driver_live_location(
    driver_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a driver's latest known location (for dashboard map). Company-scoped."""
    driver = await db.get(Driver, driver_id)
    if driver is None or driver.company_id != current_user.company_id:
        raise HTTPException(404, "Driver not found")

    # Also resolve assigned vehicle and active trip if any
    v_res = await db.execute(
        select(Vehicle).where(Vehicle.assigned_driver_id == driver.id).limit(1)
    )
    veh = v_res.scalar_one_or_none()

    t_res = await db.execute(
        select(Trip.trip_id).where(
            Trip.driver_id == driver.id,
            Trip.status == TripStatus.IN_PROGRESS
        ).limit(1)
    )
    trip_id = t_res.scalar_one_or_none()

    # Get speed from latest location point if available
    latest_pt_res = await db.execute(
        select(DriverLocation.speed, DriverLocation.heading, DriverLocation.battery_percent)
        .where(DriverLocation.driver_id == driver.id)
        .order_by(DriverLocation.timestamp.desc())
        .limit(1)
    )
    latest_pt = latest_pt_res.first()

    speed_mps = latest_pt[0] if latest_pt else None
    speed_kmh = round(speed_mps * 3.6, 1) if speed_mps is not None else None
    heading = latest_pt[1] if latest_pt else None
    battery = latest_pt[2] if latest_pt else None

    return LiveDriverLocation(
        driver_id=driver.id,
        driver_name=driver.name,
        latitude=driver.last_known_lat or 0.0,
        longitude=driver.last_known_lng or 0.0,
        speed=speed_mps,
        speed_kmh=speed_kmh,
        heading=heading,
        battery_percent=battery,
        duty_status=driver.duty_status.value if driver.duty_status else None,
        last_updated=driver.last_location_at,
        vehicle_id=veh.id if veh else None,
        vehicle_registration=veh.registration_number if veh else None,
        trip_id=trip_id,
    )


@router.get("/api/v1/tracking/driver/{driver_id}/history", response_model=List[LocationResponse])
async def get_driver_location_history(
    driver_id: int,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get driver's location history in chronological order.
    Fixes the prior bug where reverse ordering truncated the beginning of the period.
    """
    driver = await db.get(Driver, driver_id)
    if driver is None or driver.company_id != current_user.company_id:
        raise HTTPException(404, "Driver not found")

    query = select(DriverLocation).where(
        DriverLocation.driver_id == driver_id,
        DriverLocation.company_id == current_user.company_id,
        DriverLocation.latitude >= -90.0,
        DriverLocation.latitude <= 90.0,
        DriverLocation.longitude >= -180.0,
        DriverLocation.longitude <= 180.0,
    )
    if start_time:
        query = query.where(DriverLocation.timestamp >= start_time)
    if end_time:
        query = query.where(DriverLocation.timestamp <= end_time)

    # Order chronologically ascending!
    query = query.order_by(DriverLocation.timestamp.asc()).limit(limit)
    result = await db.execute(query)
    locations = list(result.scalars().all())

    responses = []
    for loc in locations:
        resp = LocationResponse.model_validate(loc)
        resp.speed_kmh = round(loc.speed * 3.6, 1) if loc.speed is not None else None
        responses.append(resp)

    return responses


@router.get("/api/v1/tracking/trip/{trip_id}/route", response_model=List[LocationResponse])
async def get_trip_route_history(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the actual GPS route for a specific trip based on trip_id or numeric ID.
    Returns points in chronological ascending order.
    """
    trip_query = select(Trip).where(Trip.company_id == current_user.company_id)
    if trip_id.isdigit():
        trip_query = trip_query.where(or_(Trip.id == int(trip_id), Trip.trip_id == trip_id))
    else:
        trip_query = trip_query.where(Trip.trip_id == trip_id)

    result = await db.execute(trip_query)
    trip = result.scalar_one_or_none()

    if trip is None:
        raise HTTPException(404, "Trip not found")

    start_time = trip.actual_start_time or trip.planned_start_time
    end_time = trip.actual_end_time or datetime.now(tz=timezone.utc)

    # Search by explicit trip_id association OR by driver time window
    conditions = [
        DriverLocation.company_id == current_user.company_id,
        DriverLocation.latitude >= -90.0,
        DriverLocation.latitude <= 90.0,
        DriverLocation.longitude >= -180.0,
        DriverLocation.longitude <= 180.0,
    ]

    trip_or_time = [DriverLocation.trip_id == trip.trip_id]
    if start_time and trip.driver_id:
        trip_or_time.append(
            and_(
                DriverLocation.driver_id == trip.driver_id,
                DriverLocation.timestamp >= start_time,
                DriverLocation.timestamp <= end_time
            )
        )
    conditions.append(or_(*trip_or_time))

    query = (
        select(DriverLocation)
        .where(and_(*conditions))
        .order_by(DriverLocation.timestamp.asc())
        .limit(3000)
    )
    loc_res = await db.execute(query)
    locations = loc_res.scalars().all()

    responses = []
    for loc in locations:
        resp = LocationResponse.model_validate(loc)
        resp.speed_kmh = round(loc.speed * 3.6, 1) if loc.speed is not None else None
        responses.append(resp)

    return responses


@router.get("/api/v1/tracking/fleet/live", response_model=List[LiveDriverLocation])
async def get_fleet_live_locations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get live locations of all active drivers in the fleet.
    Used by dashboard live maps and fleet overviews.
    """
    query = (
        select(Driver, Vehicle, Trip)
        .outerjoin(Vehicle, Vehicle.assigned_driver_id == Driver.id)
        .outerjoin(Trip, (Trip.driver_id == Driver.id) & (Trip.status == TripStatus.IN_PROGRESS))
        .where(
            Driver.last_known_lat.isnot(None),
            Driver.last_known_lng.isnot(None),
            Driver.company_id == current_user.company_id
        )
    )

    result = await db.execute(query)
    rows = result.all()

    driver_ids = [d.id for d, _, _ in rows]
    # Batch query latest speed and heading
    latest_points_map = {}
    if driver_ids:
        # Get latest point for each driver
        latest_pts_query = (
            select(DriverLocation.driver_id, DriverLocation.speed, DriverLocation.heading, DriverLocation.battery_percent)
            .where(DriverLocation.driver_id.in_(driver_ids))
            .order_by(DriverLocation.driver_id, DriverLocation.timestamp.desc())
        )
        pts_res = await db.execute(latest_pts_query)
        for d_id, spd, hdg, bat in pts_res.all():
            if d_id not in latest_points_map:
                latest_points_map[d_id] = (spd, hdg, bat)

    locations = []
    for d, v, t in rows:
        pt_info = latest_points_map.get(d.id, (None, None, None))
        spd_mps = pt_info[0]
        spd_kmh = round(spd_mps * 3.6, 1) if spd_mps is not None else None
        locations.append(LiveDriverLocation(
            driver_id=d.id,
            driver_name=d.name,
            latitude=d.last_known_lat or 0.0,
            longitude=d.last_known_lng or 0.0,
            speed=spd_mps,
            speed_kmh=spd_kmh,
            heading=pt_info[1],
            battery_percent=pt_info[2],
            duty_status=d.duty_status.value if d.duty_status else None,
            last_updated=d.last_location_at,
            vehicle_id=v.id if v else None,
            vehicle_registration=v.registration_number if v else None,
            trip_id=t.trip_id if t else None
        ))

    return locations


@router.post("/api/v1/tracking/compare-gps")
async def compare_gps_sources(
    driver_id: int,
    truck_lat: float,
    truck_lng: float,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compare truck hardware GPS with driver phone GPS.
    Alert when they significantly differ (>500m).
    Company-scoped: validates driver ownership.
    """
    driver = await db.get(Driver, driver_id)
    if driver is None or driver.company_id != current_user.company_id:
        raise HTTPException(404, "Driver not found")
    if driver.last_known_lat is None:
        raise HTTPException(404, "Driver location not available")

    distance = haversine_distance_meters(
        driver.last_known_lat, driver.last_known_lng,
        truck_lat, truck_lng
    )

    drift_detected = distance > 500.0  # 500m threshold

    return {
        "distance_meters": round(distance, 1),
        "drift_detected": drift_detected,
        "phone_gps": {"lat": driver.last_known_lat, "lng": driver.last_known_lng},
        "truck_gps": {"lat": truck_lat, "lng": truck_lng},
        "message": "GPS drift alert!" if drift_detected else "GPS sources consistent",
    }
