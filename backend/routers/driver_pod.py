"""
FleetGuard — Proof of Delivery Router
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.proof_of_delivery import ProofOfDelivery
from models.trip_domain import Trip, TripStatus
from routers.driver_mobile import get_current_driver
from models.driver_domain import Driver
from services.trip_completion_service import TripCompletionService

logger = logging.getLogger("fleetguard.pod")

router = APIRouter(prefix="/api/v1/driver-app", tags=["Proof of Delivery"])


class PodCreateRequest(BaseModel):
    signature_url: Optional[str] = None
    photos: List[str] = []
    invoice_url: Optional[str] = None
    remarks: Optional[str] = None
    receiver_name: Optional[str] = None


class PodResponse(BaseModel):
    id: int
    trip_id: int
    driver_id: int
    company_id: int
    signature_url: Optional[str]
    photos: List[str]
    invoice_url: Optional[str]
    remarks: Optional[str]
    receiver_name: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/pod/{trip_id}", response_model=PodResponse, status_code=status.HTTP_201_CREATED)
async def submit_pod(
    trip_id: int,
    payload: PodCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    """Submit proof of delivery for a trip."""
    stmt = select(Trip).where(
        Trip.id == trip_id, 
        Trip.driver_id == driver.id, 
        Trip.company_id == driver.company_id
    ).with_for_update()
    result = await db.execute(stmt)
    trip = result.scalar_one_or_none()
    if trip is None:
        raise HTTPException(404, "Trip not found")

    if trip.status in (TripStatus.CREATED, TripStatus.CANCELLED):
        raise HTTPException(400, f"Cannot submit POD for trip in status '{trip.status.value}'")

    # Check for existing POD to prevent duplicate rows / repeated side effects
    stmt_pod = select(ProofOfDelivery).where(
        ProofOfDelivery.trip_id == trip.id,
        ProofOfDelivery.company_id == driver.company_id
    ).with_for_update()
    result_pod = await db.execute(stmt_pod)
    pod = result_pod.scalar_one_or_none()

    if pod is not None:
        # Idempotent update on existing POD without re-triggering completion side effects
        if payload.signature_url is not None:
            pod.signature_url = payload.signature_url
        if payload.photos:
            pod.photos = payload.photos
        if payload.invoice_url is not None:
            pod.invoice_url = payload.invoice_url
        if payload.remarks is not None:
            pod.remarks = payload.remarks
        if payload.receiver_name is not None:
            pod.receiver_name = payload.receiver_name

        await db.commit()
        await db.refresh(pod)
        return PodResponse.model_validate(pod)

    # First-time POD submission
    pod = ProofOfDelivery(
        trip_id=trip.id,
        driver_id=driver.id,
        company_id=driver.company_id,
        signature_url=payload.signature_url,
        photos=payload.photos,
        invoice_url=payload.invoice_url,
        remarks=payload.remarks,
        receiver_name=payload.receiver_name,
    )
    db.add(pod)

    # Complete the trip if not already completed
    if trip.status != TripStatus.COMPLETED:
        trip.status = TripStatus.COMPLETED
        trip.actual_end_time = datetime.now(timezone.utc)

        from services.trip_service import create_trip_operational_event
        from models.operational_event import EventType
        event = create_trip_operational_event(
            company_id=driver.company_id,
            event_type=EventType.TRIP_COMPLETED,
            trip_business_id=trip.trip_id,
            payload={"trigger": "pod_submission"},
            created_by=f"driver:{driver.id}"
        )
        db.add(event)

        # Trigger canonical telemetry calculation in background
        background_tasks.add_task(TripCompletionService.run_telemetry_finalization_task, trip.id)

    await db.commit()
    await db.refresh(pod)

    logger.info(f"POD submitted for trip {trip_id}")

    return PodResponse.model_validate(pod)



@router.get("/pod/{trip_id}", response_model=PodResponse)
async def get_pod(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    """Get POD for a specific trip."""
    result = await db.execute(
        select(ProofOfDelivery).where(
            ProofOfDelivery.trip_id == trip_id,
            ProofOfDelivery.driver_id == driver.id,
            ProofOfDelivery.company_id == driver.company_id
        )
    )
    pod = result.scalar_one_or_none()

    if pod is None:
        raise HTTPException(404, "POD not found for trip")

    return PodResponse(
        id=pod.id,
        trip_id=pod.trip_id,
        driver_id=pod.driver_id,
        company_id=pod.company_id,
        signature_url=pod.signature_url,
        photos=pod.photos or [],
        invoice_url=pod.invoice_url,
        remarks=pod.remarks,
        receiver_name=pod.receiver_name,
        created_at=pod.created_at,
    )
