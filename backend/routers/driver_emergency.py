"""
FleetGuard — Driver Emergency / SOS & Assistance Router
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.emergency import EmergencyAlert, EmergencyStatus
from models.driver_domain import Driver
from models.support_domain import (
    SupportTicket,
    SupportTicketMessage,
    RequesterType,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    MessageType,
)
from schemas.support_domain import SupportTicketResponse
from routers.driver_mobile import get_current_driver

logger = logging.getLogger("fleetguard.emergency")

router = APIRouter(prefix="/api/v1/driver-app", tags=["Driver Emergency"])


class SosRequest(BaseModel):
    driver_id: Optional[int] = None
    company_id: Optional[int] = None
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
    ticket_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DriverAssistanceRequest(BaseModel):
    title: str
    description: str
    category: Optional[TicketCategory] = TicketCategory.TECHNICAL
    priority: Optional[TicketPriority] = TicketPriority.HIGH
    vehicle_id: Optional[int] = None
    trip_id: Optional[int] = None


@router.post("/sos", response_model=SosResponse, status_code=status.HTTP_201_CREATED)
async def trigger_sos(
    payload: SosRequest,
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger emergency SOS alert.
    1. Records EmergencyAlert for live telemetry and map tracking.
    2. Atomically opens an URGENT SupportTicket in Super Admin support queue.
    """
    sos = EmergencyAlert(
        driver_id=driver.id,
        company_id=driver.company_id,
        vehicle_id=payload.vehicle_id,
        trip_id=payload.trip_id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        status=EmergencyStatus.ACTIVE,
        message=payload.message,
    )
    db.add(sos)
    await db.flush()

    ticket_code = f"SOS-{uuid.uuid4().hex[:8].upper()}"
    ticket = SupportTicket(
        ticket_id=ticket_code,
        title=f"🚨 EMERGENCY SOS - Driver {driver.name} (#{driver.id})",
        description=f"Emergency distress alert triggered by driver {driver.name} (Phone: {driver.phone_number}). "
                    f"Live GPS: ({payload.latitude}, {payload.longitude}). "
                    f"Message: {payload.message or 'Immediate assistance required.'}",
        category=TicketCategory.COMPLAINT,
        priority=TicketPriority.URGENT,
        status=TicketStatus.OPEN,
        requester_type=RequesterType.DRIVER,
        requester_id=driver.id,
        requester_name=driver.name,
        requester_phone=driver.phone_number,
        company_id=driver.company_id,
        driver_id=driver.id,
        vehicle_id=payload.vehicle_id,
        trip_id=payload.trip_id,
    )
    db.add(ticket)
    await db.flush()

    # Create initial message thread
    initial_msg = SupportTicketMessage(
        ticket_id=ticket.id,
        content=f"EMERGENCY SOS ALERT: Lat {payload.latitude}, Lng {payload.longitude}. Note: {payload.message}",
        message_type=MessageType.PUBLIC,
        sender_type=RequesterType.DRIVER,
        sender_id=driver.id,
        sender_name=driver.name,
    )
    db.add(initial_msg)

    await db.commit()
    await db.refresh(sos)

    logger.critical(
        f"🚨 EMERGENCY SOS triggered by Driver #{driver.id} at ({payload.latitude}, {payload.longitude}) [Ticket {ticket_code}]"
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
        ticket_id=ticket_code,
        created_at=sos.created_at,
    )


@router.post("/assistance", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
async def request_assistance(
    payload: DriverAssistanceRequest,
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """
    Driver submits an assistance or technical support request.
    Creates a SupportTicket visible in the Super Admin inbox with requester_type=DRIVER.
    """
    ticket_code = f"DRV-{uuid.uuid4().hex[:8].upper()}"
    ticket = SupportTicket(
        ticket_id=ticket_code,
        title=payload.title,
        description=payload.description,
        category=payload.category or TicketCategory.TECHNICAL,
        priority=payload.priority or TicketPriority.HIGH,
        status=TicketStatus.OPEN,
        requester_type=RequesterType.DRIVER,
        requester_id=driver.id,
        requester_name=driver.name,
        requester_phone=driver.phone_number,
        company_id=driver.company_id,
        driver_id=driver.id,
        vehicle_id=payload.vehicle_id,
        trip_id=payload.trip_id,
    )
    db.add(ticket)
    await db.flush()

    initial_msg = SupportTicketMessage(
        ticket_id=ticket.id,
        content=payload.description,
        message_type=MessageType.PUBLIC,
        sender_type=RequesterType.DRIVER,
        sender_id=driver.id,
        sender_name=driver.name,
    )
    db.add(initial_msg)

    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/assistance", response_model=List[SupportTicketResponse])
async def list_driver_assistance(
    driver: Driver = Depends(get_current_driver),
    db: AsyncSession = Depends(get_db),
):
    """List assistance tickets created by the authenticated driver."""
    result = await db.execute(
        select(SupportTicket)
        .where(
            SupportTicket.driver_id == driver.id,
            SupportTicket.company_id == driver.company_id
        )
        .order_by(desc(SupportTicket.created_at))
    )
    return result.scalars().all()


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
