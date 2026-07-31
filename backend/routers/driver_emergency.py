"""
FleetGuard — Driver Emergency / SOS Router
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.emergency import EmergencyAlert, EmergencyStatus

logger = logging.getLogger("fleetguard.emergency")

router = APIRouter(prefix="/api/v1/driver-app", tags=["Driver Emergency"])


class SosRequest(BaseModel):
    driver_id: int
    company_id: int
    vehicle_id: Optional[int] = None
    trip_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    message: Optional[str] = "EMERGENCY SOS: Driver triggered distress alert!"


class SosResponse(BaseModel):
    id: int
    driver_id: int
    company_id: int
    vehicle_id: Optional[int]
    trip_id: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    status: str
    message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/sos", response_model=SosResponse, status_code=status.HTTP_201_CREATED)
async def trigger_sos(
    payload: SosRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger emergency SOS alert.
    Immediately records live location and alerts fleet manager.
    """
    sos = EmergencyAlert(
        driver_id=payload.driver_id,
        company_id=payload.company_id,
        vehicle_id=payload.vehicle_id,
        trip_id=payload.trip_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=EmergencyStatus.ACTIVE,
        message=payload.message,
    )

    db.add(sos)
    await db.commit()
    await db.refresh(sos)

    logger.critical(
        f"🚨 EMERGENCY SOS triggered by Driver #{payload.driver_id} at ({payload.latitude}, {payload.longitude})"
    )

    return SosResponse(
        id=sos.id,
        driver_id=sos.driver_id,
        company_id=sos.company_id,
        vehicle_id=sos.vehicle_id,
        trip_id=sos.trip_id,
        latitude=sos.latitude,
        longitude=sos.longitude,
        status=sos.status.value,
        message=sos.message,
        created_at=sos.created_at,
    )


@router.get("/sos/active", response_model=List[SosResponse])
async def list_active_sos(
    company_id: int,
    db: AsyncSession = Depends(get_db),
):
    """List active emergency SOS alerts for fleet dashboard."""
    result = await db.execute(
        select(EmergencyAlert)
        .where(
            EmergencyAlert.company_id == company_id,
            EmergencyAlert.status == EmergencyStatus.ACTIVE,
        )
        .order_by(desc(EmergencyAlert.created_at))
    )
    alerts = result.scalars().all()

    return [
        SosResponse(
            id=a.id,
            driver_id=a.driver_id,
            company_id=a.company_id,
            vehicle_id=a.vehicle_id,
            trip_id=a.trip_id,
            latitude=a.latitude,
            longitude=a.longitude,
            status=a.status.value,
            message=a.message,
            created_at=a.created_at,
        )
        for a in alerts
    ]
