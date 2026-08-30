"""
FleetGuard — Proof of Delivery Router
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.proof_of_delivery import ProofOfDelivery
from models.trip_domain import Trip, TripStatus
from routers.driver_mobile import get_current_driver
from models.driver_domain import Driver

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
    db: AsyncSession = Depends(get_db),
    driver: Driver = Depends(get_current_driver),
):
    """Submit proof of delivery for a trip."""
    trip = await db.get(Trip, trip_id)
    if trip is None or trip.driver_id != driver.id or trip.company_id != driver.company_id:
        raise HTTPException(404, "Trip not found")

    pod = ProofOfDelivery(
        trip_id=trip_id,
        driver_id=driver.id,
        company_id=driver.company_id,
        signature_url=payload.signature_url,
        photos=payload.photos,
        invoice_url=payload.invoice_url,
        remarks=payload.remarks,
        receiver_name=payload.receiver_name,
    )

    db.add(pod)

    # Mark trip as completed
    trip.status = TripStatus.COMPLETED
    trip.actual_end_time = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(pod)

    logger.info(f"POD submitted for trip {trip_id}")

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
