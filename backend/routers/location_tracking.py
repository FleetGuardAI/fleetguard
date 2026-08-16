"""
FleetGuard — Location Tracking API Router

Handles GPS location ingestion from driver phones and provides
live tracking endpoints for the dashboard.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.driver_domain import Driver
from models.location_tracking import DriverLocation, LocationSource
from models.trip_domain import Trip, TripStatus
from models.vehicle_domain import Vehicle
from models.user import User
from services.auth_service import get_current_user

logger = logging.getLogger("fleetguard.tracking")

router = APIRouter(tags=["Location Tracking"])


# ==========================================================================
# Schemas
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
    driver_id: int
    locations: List[LocationPoint]

class LocationResponse(BaseModel):
    id: int
    driver_id: int
    latitude: float
    longitude: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None
    timestamp: datetime
    battery_percent: Optional[int] = None
    activity_state: Optional[str] = None
    source: str

    model_config = {"from_attributes": True}

class LiveDriverLocation(BaseModel):
    driver_id: int
    driver_name: str
    latitude: float
    longitude: float
    speed: Optional[float] = None
    heading: Optional[float] = None
    battery_percent: Optional[int] = None
    duty_status: Optional[str] = None
    last_updated: Optional[datetime] = None
    vehicle_id: Optional[int] = None
    vehicle_registration: Optional[str] = None
    trip_id: Optional[str] = None


# ==========================================================================
# Driver App Endpoints
# ==========================================================================

@router.post("/api/v1/driver-app/location/batch", status_code=201)
async def batch_upload_locations(
    payload: LocationBatchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Batch upload GPS locations from driver's phone.
    Accepts queued offline locations for sync.
    """
    driver = await db.get(Driver, payload.driver_id)
    if driver is None:
        raise HTTPException(404, "Driver not found")

    locations_added = 0
    latest_location = None

    for loc in payload.locations:
        try:
            ts = datetime.fromisoformat(loc.timestamp.replace("Z", "+00:00"))
        except ValueError:
            ts = datetime.now(tz=timezone.utc)

        db_loc = DriverLocation(
            driver_id=payload.driver_id,
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

    logger.info(f"Driver {payload.driver_id}: {locations_added} locations synced")
    return {"message": f"{locations_added} locations recorded"}


# ==========================================================================
# Dashboard / Tracking Endpoints
# ==========================================================================

@router.get("/api/v1/tracking/driver/{driver_id}/live", response_model=LiveDriverLocation)
async def get_driver_live_location(
    driver_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a driver's latest known location (for dashboard map)."""
    driver = await db.get(Driver, driver_id)
    if driver is None:
        raise HTTPException(404, "Driver not found")

    return LiveDriverLocation(
        driver_id=driver.id,
        driver_name=driver.name,
        latitude=driver.last_known_lat or 0.0,
        longitude=driver.last_known_lng or 0.0,
        duty_status=driver.duty_status.value if driver.duty_status else None,
        last_updated=driver.last_location_at,
    )


@router.get("/api/v1/tracking/driver/{driver_id}/history", response_model=List[LocationResponse])
async def get_driver_location_history(
    driver_id: int,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Get driver's location history (most recent first)."""
    result = await db.execute(
        select(DriverLocation)
        .where(DriverLocation.driver_id == driver_id)
        .order_by(desc(DriverLocation.timestamp))
        .limit(limit)
    )
    locations = result.scalars().all()

    return [LocationResponse(
        id=loc.id,
        driver_id=loc.driver_id,
        latitude=loc.latitude,
        longitude=loc.longitude,
        speed=loc.speed,
        heading=loc.heading,
        accuracy=loc.accuracy,
        timestamp=loc.timestamp,
        battery_percent=loc.battery_percent,
        activity_state=loc.activity_state,
        source=loc.source.value,
    ) for loc in locations]


@router.get("/api/v1/tracking/fleet/live", response_model=List[LiveDriverLocation])
async def get_fleet_live_locations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get live locations of all active drivers in the fleet.
    Used by the dashboard's live map view.
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

    return [LiveDriverLocation(
        driver_id=d.id,
        driver_name=d.name,
        latitude=d.last_known_lat or 0.0,
        longitude=d.last_known_lng or 0.0,
        duty_status=d.duty_status.value if d.duty_status else None,
        last_updated=d.last_location_at,
        vehicle_id=v.id if v else None,
        vehicle_registration=v.registration_number if v else None,
        trip_id=t.trip_id if t else None
    ) for d, v, t in rows]


@router.post("/api/v1/tracking/compare-gps")
async def compare_gps_sources(
    driver_id: int,
    truck_lat: float,
    truck_lng: float,
    db: AsyncSession = Depends(get_db),
):
    """
    Compare truck hardware GPS with driver phone GPS.
    Alert when they significantly differ (>500m).
    """
    driver = await db.get(Driver, driver_id)
    if driver is None or driver.last_known_lat is None:
        raise HTTPException(404, "Driver location not available")

    # Haversine distance calculation (simplified)
    import math
    R = 6371000  # Earth radius in meters

    lat1, lon1 = math.radians(driver.last_known_lat), math.radians(driver.last_known_lng)
    lat2, lon2 = math.radians(truck_lat), math.radians(truck_lng)
    dlat, dlon = lat2 - lat1, lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    distance = R * c

    drift_detected = distance > 500  # 500m threshold

    return {
        "distance_meters": round(distance, 1),
        "drift_detected": drift_detected,
        "phone_gps": {"lat": driver.last_known_lat, "lng": driver.last_known_lng},
        "truck_gps": {"lat": truck_lat, "lng": truck_lng},
        "message": "GPS drift alert!" if drift_detected else "GPS sources consistent",
    }
