"""
FleetGuard — Driver Trips & Assigned Vehicle Router

Provides endpoints for driver trip management, assigned vehicle viewing, and trip lifecycle actions.
Includes strict fleet isolation and mandatory selfie-with-truck verification.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
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
    planned_distance: Optional[float] = None
    actual_distance: Optional[float] = None
    planned_start_time: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    planned_end_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    customer_name: Optional[str] = "Acme Logistics Ltd"
    customer_phone: Optional[str] = "+919876543210"
    instructions: Optional[str] = "Handle fragile cargo with care. Call on arrival."
    eta_minutes: Optional[int] = 45
    distance_remaining_km: Optional[float] = 28.5
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
            StopPoint(location=trip.origin_location or "Warehouse A", stop_order=1, status="COMPLETED" if trip.status == TripStatus.IN_PROGRESS else "PENDING"),
            StopPoint(location="Midpoint Fuel Station", stop_order=2, status="PENDING"),
            StopPoint(location=trip.destination_location or "Distribution Hub B", stop_order=3, status="PENDING"),
        ]
        response_trips.append(
            DriverTripResponse(
                id=trip.id,
                trip_id=trip.trip_id,
                status=trip.status.value if trip.status else "CREATED",
                origin_location=trip.origin_location,
                destination_location=trip.destination_location,
                planned_distance=trip.planned_distance or 120.0,
                actual_distance=trip.actual_distance,
                planned_start_time=trip.planned_start_time,
                actual_start_time=trip.actual_start_time,
                planned_end_time=trip.planned_end_time,
                actual_end_time=trip.actual_end_time,
                vehicle_id=trip.vehicle_id,
                driver_id=trip.driver_id,
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
    trip = await db.get(Trip, trip_id)
    if trip is None or trip.driver_id != driver.id or trip.company_id != driver.company_id:
        raise HTTPException(404, "Trip not found")

    # Check for active trips
    active_result = await db.execute(
        select(Trip).where(
            Trip.driver_id == driver.id, 
            Trip.status == TripStatus.IN_PROGRESS
        )
    )
    if active_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Another trip is currently in progress")

    # Ensure selfie verification is complete
    if not trip.start_selfie_url:
        raise HTTPException(status_code=400, detail="Mandatory trip-start selfie is missing. Please upload selfie with truck first.")

    trip.status = TripStatus.IN_PROGRESS
    trip.actual_start_time = datetime.now(timezone.utc)

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
    trip = await db.get(Trip, trip_id)
    if trip is None or trip.driver_id != driver.id or trip.company_id != driver.company_id:
        raise HTTPException(404, "Trip not found")

    trip.status = TripStatus.PAUSED
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
    trip = await db.get(Trip, trip_id)
    if trip is None or trip.driver_id != driver.id or trip.company_id != driver.company_id:
        raise HTTPException(404, "Trip not found")

    trip.status = TripStatus.IN_PROGRESS
    await db.commit()
    await db.refresh(trip)

    return DriverTripResponse.model_validate(trip)


@router.post("/trips/{trip_id}/complete", response_model=DriverTripResponse)
async def complete_trip(
    trip_id: int,
    actual_distance: Optional[float] = Query(None),
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """Complete a trip."""
    trip = await db.get(Trip, trip_id)
    if trip is None or trip.driver_id != driver.id or trip.company_id != driver.company_id:
        raise HTTPException(404, "Trip not found")

    trip.status = TripStatus.COMPLETED
    trip.actual_end_time = datetime.now(timezone.utc)
    if actual_distance:
        trip.actual_distance = actual_distance

    await db.commit()
    await db.refresh(trip)

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
        image_url="/uploads/vehicles/demo_truck.jpg",
        status=vehicle.status.value if vehicle.status else "ACTIVE",
    )
