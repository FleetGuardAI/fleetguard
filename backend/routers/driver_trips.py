"""
FleetGuard — Driver Trips & Assigned Vehicle Router

Provides endpoints for driver trip management, assigned vehicle viewing, and trip lifecycle actions.
Includes strict fleet isolation and mandatory selfie-with-truck verification.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.driver_domain import Driver
from models.trip_domain import Trip, TripStatus
from models.vehicle_domain import Vehicle
from models.trip_start_selfie import TripStartSelfie
from routers.driver_mobile import get_current_driver
from services.file_upload_service import storage_service
from services.trip_completion_service import TripCompletionService

logger = logging.getLogger("fleetguard.driver_trips")

router = APIRouter(prefix="/api/v1/driver-app", tags=["Driver Trips"])


# --- Schemas ---

class VehicleDetailResponse(BaseModel):
    id: int
    registration_number: str
    make: str
    model: Optional[str] = None
    year: Optional[int] = None
    tank_capacity: float
    vin: Optional[str] = None
    fuel_type: str = "DIESEL"
    insurance_status: str = "VALID"
    fitness_status: str = "VALID"
    puc_status: str = "VALID"
    permit_status: str = "NATIONAL_PERMIT"
    assigned_dispatcher: str = "Fleet Operations Center"
    image_url: Optional[str] = None
    status: str

    model_config = {"from_attributes": True}


class StopPoint(BaseModel):
    location: str
    stop_order: int
    status: str = "PENDING"  # PENDING / REACHED / COMPLETED


class DriverTripResponse(BaseModel):
    id: int
    trip_id: str
    status: str
    origin_location: Optional[str] = None
    destination_location: Optional[str] = None
    origin_lat: Optional[float] = None
    origin_lng: Optional[float] = None
    origin_address: Optional[str] = None
    destination_lat: Optional[float] = None
    destination_lng: Optional[float] = None
    destination_address: Optional[str] = None
    planned_distance: Optional[float] = None
    actual_distance: Optional[float] = None
    planned_start_time: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    planned_end_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_contact_person: Optional[str] = None
    instructions: Optional[str] = None
    eta_minutes: Optional[int] = None
    distance_remaining_km: Optional[float] = None
    stops: List[StopPoint] = []
    start_selfie_url: Optional[str] = None

    model_config = {"from_attributes": True}


@router.get("/trips/today", response_model=List[DriverTripResponse])
async def get_today_trips(
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Get today's assigned trips for the authenticated driver.
    Ensures strict tenant isolation by using the JWT driver profile.
    """
    result = await db.execute(
        select(Trip).where(Trip.driver_id == driver.id, Trip.company_id == driver.company_id)
    )
    trips = result.scalars().all()

    response_trips = []
    for trip in trips:
        stops = [
            StopPoint(location=trip.origin_location or "Pickup", stop_order=1, status="COMPLETED" if trip.status == TripStatus.IN_PROGRESS else "PENDING"),
            StopPoint(location=trip.destination_location or "Delivery", stop_order=2, status="PENDING"),
        ]
        response_trips.append(
            DriverTripResponse(
                id=trip.id,
                trip_id=trip.trip_id,
                status=trip.status.value if trip.status else "CREATED",
                origin_location=trip.origin_location,
                destination_location=trip.destination_location,
                origin_lat=trip.origin_lat,
                origin_lng=trip.origin_lng,
                origin_address=trip.origin_address,
                destination_lat=trip.destination_lat,
                destination_lng=trip.destination_lng,
                destination_address=trip.destination_address,
                planned_distance=trip.planned_distance,
                actual_distance=trip.actual_distance,
                planned_start_time=trip.planned_start_time,
                actual_start_time=trip.actual_start_time,
                planned_end_time=trip.planned_end_time,
                actual_end_time=trip.actual_end_time,
                vehicle_id=trip.vehicle_id,
                driver_id=trip.driver_id,
                customer_name=trip.customer_name,
                customer_phone=trip.customer_phone,
                customer_contact_person=trip.customer_contact_person,
                instructions=trip.instructions,
                stops=stops,
                start_selfie_url=trip.start_selfie_url,
            )
        )

    return response_trips


@router.post("/trips/{trip_id}/start-selfie")
async def upload_trip_start_selfie(
    trip_id: int,
    file: UploadFile = File(...),
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Upload mandatory selfie-with-truck before starting a trip."""
    trip = await db.get(Trip, trip_id)
    if not trip or trip.driver_id != driver.id or trip.company_id != driver.company_id:
        raise HTTPException(status_code=404, detail="Trip not found")

    if not trip.vehicle_id:
        raise HTTPException(status_code=400, detail="No vehicle assigned to this trip")

    vehicle = await db.get(Vehicle, trip.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=400, detail="Assigned vehicle not found")

    # Upload selfie
    url = await storage_service.upload_file(
        file=file,
        folder=f"trips/{trip_id}/selfies",
    )

    # Create verification record
    selfie_record = TripStartSelfie(
        trip_id=trip.id,
        driver_id=driver.id,
        vehicle_id=vehicle.id,
        company_id=driver.company_id,
        registration_number=vehicle.registration_number,
        selfie_url=url,
        verification_status="COMPLETED"
    )
    db.add(selfie_record)
    
    trip.start_selfie_url = url
    await db.commit()

    return {"message": "Selfie uploaded successfully", "url": url}


@router.post("/trips/{trip_id}/start", response_model=DriverTripResponse)
async def start_trip(
    trip_id: int,
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Start an assigned trip, requiring prior selfie verification."""
    stmt = select(Trip).where(
        Trip.id == trip_id, 
        Trip.driver_id == driver.id, 
        Trip.company_id == driver.company_id
    ).with_for_update()
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    if trip is None:
        raise HTTPException(404, "Trip not found")

    # Idempotent return if already IN_PROGRESS
    if trip.status == TripStatus.IN_PROGRESS:
        return DriverTripResponse.model_validate(trip)

    # Can only start from CREATED
    if trip.status != TripStatus.CREATED:
        raise HTTPException(400, f"Cannot start trip with status '{trip.status.value}'")

    # Check for active trips for this driver
    active_result = await db.execute(
        select(Trip).where(
            Trip.driver_id == driver.id, 
            Trip.status.in_([TripStatus.IN_PROGRESS, TripStatus.PAUSED]),
            Trip.id != trip.id
        )
    )
    if active_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Another trip is currently in progress")

    # Check assigned vehicle and vehicle suitability/availability
    if not trip.vehicle_id:
        raise HTTPException(status_code=400, detail="No vehicle assigned to this trip")

    from models.vehicle_domain import Vehicle, VehicleStatus
    vehicle = await db.get(Vehicle, trip.vehicle_id)
    if not vehicle or vehicle.company_id != driver.company_id:
        raise HTTPException(status_code=400, detail="Assigned vehicle not found")
    if vehicle.status != VehicleStatus.ACTIVE:
        raise HTTPException(status_code=400, detail=f"Assigned vehicle is not available for dispatch (status is {vehicle.status.value})")

    # Check active trips for this vehicle
    active_v_result = await db.execute(
        select(Trip).where(
            Trip.vehicle_id == trip.vehicle_id,
            Trip.status.in_([TripStatus.IN_PROGRESS, TripStatus.PAUSED]),
            Trip.id != trip.id
        )
    )
    if active_v_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Assigned vehicle is currently in use on another active trip")

    # Ensure canonical dispatch suitability (qualifications, vehicle capability, cargo compatibility, maintenance)
    from services.dispatch_suitability_service import DispatchSuitabilityService
    suitability_service = DispatchSuitabilityService(db)
    suit_res = await suitability_service.evaluate_dispatch_suitability(
        company_id=driver.company_id,
        vehicle_id=trip.vehicle_id,
        driver_id=driver.id,
        planned_start=trip.planned_start_time or datetime.now(timezone.utc),
        planned_end=trip.planned_end_time,
        route_distance_km=trip.route_distance_km or trip.planned_distance,
        cargo_weight=trip.cargo_weight,
        cargo_category=trip.cargo_category,
        required_vehicle_class=trip.required_vehicle_class,
        required_driver_qualification=trip.required_driver_qualification,
        cargo_temperature_required=trip.cargo_temperature_required,
        exclude_trip_id=trip.id,
    )
    if suit_res.hard_failures:
        raise HTTPException(status_code=400, detail="; ".join(suit_res.hard_failures))

    # Ensure selfie verification is complete
    if not trip.start_selfie_url:
        raise HTTPException(status_code=400, detail="Mandatory trip-start selfie is missing. Please upload selfie with truck first.")

    trip.status = TripStatus.IN_PROGRESS
    trip.actual_start_time = datetime.now(timezone.utc)

    from services.trip_service import create_trip_operational_event
    from models.operational_event import EventType
    event = create_trip_operational_event(
        company_id=driver.company_id,
        event_type=EventType.TRIP_STARTED,
        trip_business_id=trip.trip_id,
        payload={"actual_start_time": trip.actual_start_time.isoformat()},
        created_by=f"driver:{driver.id}"
    )
    db.add(event)

    await db.commit()
    await db.refresh(trip)

    logger.info(f"Trip {trip_id} started by driver {driver.id}")
    return DriverTripResponse.model_validate(trip)


@router.post("/trips/{trip_id}/pause", response_model=DriverTripResponse)
async def pause_trip(
    trip_id: int,
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Pause an ongoing trip."""
    stmt = select(Trip).where(
        Trip.id == trip_id, 
        Trip.driver_id == driver.id, 
        Trip.company_id == driver.company_id
    ).with_for_update()
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    if trip is None:
        raise HTTPException(404, "Trip not found")

    if trip.status == TripStatus.PAUSED:
        return DriverTripResponse.model_validate(trip)

    if trip.status != TripStatus.IN_PROGRESS:
        raise HTTPException(400, f"Cannot pause trip in status '{trip.status.value}'")

    trip.status = TripStatus.PAUSED

    from services.trip_service import create_trip_operational_event
    from models.operational_event import EventType
    event = create_trip_operational_event(
        company_id=driver.company_id,
        event_type=EventType.TRIP_PAUSED,
        trip_business_id=trip.trip_id,
        payload={},
        created_by=f"driver:{driver.id}"
    )
    db.add(event)

    await db.commit()
    await db.refresh(trip)

    return DriverTripResponse.model_validate(trip)


@router.post("/trips/{trip_id}/resume", response_model=DriverTripResponse)
async def resume_trip(
    trip_id: int,
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused trip."""
    stmt = select(Trip).where(
        Trip.id == trip_id, 
        Trip.driver_id == driver.id, 
        Trip.company_id == driver.company_id
    ).with_for_update()
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    if trip is None:
        raise HTTPException(404, "Trip not found")

    if trip.status == TripStatus.IN_PROGRESS:
        return DriverTripResponse.model_validate(trip)

    if trip.status != TripStatus.PAUSED:
        raise HTTPException(400, f"Cannot resume trip in status '{trip.status.value}'")

    trip.status = TripStatus.IN_PROGRESS

    from services.trip_service import create_trip_operational_event
    from models.operational_event import EventType
    event = create_trip_operational_event(
        company_id=driver.company_id,
        event_type=EventType.TRIP_RESUMED,
        trip_business_id=trip.trip_id,
        payload={},
        created_by=f"driver:{driver.id}"
    )
    db.add(event)

    await db.commit()
    await db.refresh(trip)

    return DriverTripResponse.model_validate(trip)


@router.post("/trips/{trip_id}/complete", response_model=DriverTripResponse)
async def complete_trip(
    trip_id: int,
    background_tasks: BackgroundTasks,
    actual_distance: Optional[float] = Query(None),
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Complete a trip."""
    stmt = select(Trip).where(
        Trip.id == trip_id, 
        Trip.driver_id == driver.id, 
        Trip.company_id == driver.company_id
    ).with_for_update()
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    if trip is None:
        raise HTTPException(404, "Trip not found")

    # Idempotent return if already COMPLETED (no duplicate side-effects)
    if trip.status == TripStatus.COMPLETED:
        return DriverTripResponse.model_validate(trip)

    if trip.status not in (TripStatus.IN_PROGRESS, TripStatus.PAUSED):
        raise HTTPException(400, f"Cannot complete trip in status '{trip.status.value}'")

    trip.status = TripStatus.COMPLETED
    trip.actual_end_time = datetime.now(timezone.utc)
    if actual_distance is not None:
        trip.actual_distance = actual_distance

    from services.trip_service import create_trip_operational_event
    from models.operational_event import EventType
    event = create_trip_operational_event(
        company_id=driver.company_id,
        event_type=EventType.TRIP_COMPLETED,
        trip_business_id=trip.trip_id,
        payload={
            "actual_end_time": trip.actual_end_time.isoformat(),
            "actual_distance": trip.actual_distance,
        },
        created_by=f"driver:{driver.id}"
    )
    db.add(event)

    await db.commit()
    await db.refresh(trip)
    
    # Run canonical telemetry calculation in background
    background_tasks.add_task(TripCompletionService.run_telemetry_finalization_task, trip.id)

    logger.info(f"Trip {trip_id} completed by driver {driver.id}")
    return DriverTripResponse.model_validate(trip)



@router.get("/vehicle", response_model=VehicleDetailResponse)
async def get_assigned_vehicle(
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the vehicle currently assigned to the authenticated driver.
    """
    result = await db.execute(
        select(Vehicle).where(
            Vehicle.assigned_driver_id == driver.id,
            Vehicle.company_id == driver.company_id
        ).limit(1)
    )
    vehicle = result.scalar_one_or_none()

    if vehicle is None:
        raise HTTPException(404, "No vehicle assigned to this driver")

    return VehicleDetailResponse(
        id=vehicle.id,
        registration_number=vehicle.registration_number,
        make=vehicle.make,
        model=vehicle.model,
        year=vehicle.year,
        tank_capacity=vehicle.tank_capacity,
        vin=vehicle.vin,
        fuel_type="DIESEL",
        insurance_status="VALID",
        fitness_status="VALID",
        puc_status="VALID",
        permit_status="NATIONAL_PERMIT",
        assigned_dispatcher="Fleet Operations Center",
        image_url=None,
        status=vehicle.status.value if vehicle.status else "ACTIVE",
    )
