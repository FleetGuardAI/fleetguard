"""
FleetGuard — Tickets (Expenses) API Router
CRUD operations and approval workflow for expense tickets.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database import get_db, get_uow
from models.ticket import Ticket, TicketStatus, RiskLevel
from models.operational_event import EventType, EntityType, CaptureMethod
from schemas.operational_event import OperationalEventCreate
from routers.operational_events import get_event_service
from services.operational_event_service import OperationalEventService
from models.driver_domain import Driver
from models.vehicle_domain import Vehicle
from schemas.ticket import (
    TicketCreate,
    TicketUpdate,
    TicketResponse,
    TicketApproval,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


def _ticket_to_response(ticket: Ticket, driver_name: str = None, truck_plate: str = None) -> TicketResponse:
    """Convert a Ticket ORM instance to a TicketResponse schema."""
    return TicketResponse(
        id=ticket.id,
        truck_id=ticket.vehicle_id,
        driver_id=ticket.driver_id,
        issue_type=ticket.issue_type,
        vendor_name=ticket.vendor_name,
        amount=ticket.amount,
        fair_price=ticket.fair_price,
        description=ticket.description,
        location_lat=ticket.location_lat,
        location_lng=ticket.location_lng,
        location_name=ticket.location_name,
        receipt_url=ticket.receipt_url,
        status=ticket.status.value,
        risk_level=ticket.risk_level.value,
        risk_reasons=ticket.risk_reasons,
        is_duplicate=ticket.is_duplicate,
        expense_date=ticket.expense_date,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        payout_reference=ticket.payout_reference,
        driver_name=driver_name,
        truck_plate=truck_plate,
    )


@router.get("", response_model=list[TicketResponse])
async def list_tickets(
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected"),
    risk_level: Optional[str] = Query(None, description="Filter by risk: Low, Medium, High, Critical"),
    driver_id: Optional[int] = Query(None),
    truck_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow = Depends(get_uow),
) -> list[TicketResponse]:
    """List all tickets with optional filters. Returns joined driver/truck names."""
    query = (
        select(Ticket, Driver.name, Vehicle.registration_number)
        .join(Driver, Ticket.driver_id == Driver.id)
        .join(Vehicle, Ticket.vehicle_id == Vehicle.id)
    )

    if status:
        try:
            status_enum = TicketStatus(status)
            query = query.where(Ticket.status == status_enum)
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")

    if risk_level:
        try:
            risk_enum = RiskLevel(risk_level)
            query = query.where(Ticket.risk_level == risk_enum)
        except ValueError:
            raise HTTPException(400, f"Invalid risk_level: {risk_level}")

    if driver_id:
        query = query.where(Ticket.driver_id == driver_id)
    if truck_id:
        query = query.where(Ticket.vehicle_id == truck_id)

    query = query.order_by(Ticket.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    return [
        _ticket_to_response(ticket, driver_name, truck_plate)
        for ticket, driver_name, truck_plate in rows
    ]


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int, uow = Depends(get_uow)) -> TicketResponse:
    """Get a single ticket by ID."""
    result = await db.execute(
        select(Ticket, Driver.name, Vehicle.registration_number)
        .join(Driver, Ticket.driver_id == Driver.id)
        .join(Vehicle, Ticket.vehicle_id == Vehicle.id)
        .where(Ticket.id == ticket_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, f"Ticket {ticket_id} not found")

    ticket, driver_name, truck_plate = row
    return _ticket_to_response(ticket, driver_name, truck_plate)


@router.post("", response_model=TicketResponse, status_code=201)
async def create_ticket(
    payload: TicketCreate,
    uow = Depends(get_uow),
) -> TicketResponse:
    """Create a new expense ticket."""
    # Verify truck and driver exist
    vehicle = await db.get(Vehicle, payload.truck_id)
    if not vehicle:
        raise HTTPException(404, f"Vehicle {payload.truck_id} not found")

    driver = await db.get(Driver, payload.driver_id)
    if not driver:
        raise HTTPException(404, f"Driver {payload.driver_id} not found")

    ticket = Ticket(
        vehicle_id=payload.truck_id,
        driver_id=payload.driver_id,
        issue_type=payload.issue_type,
        vendor_name=payload.vendor_name,
        amount=payload.amount,
        description=payload.description,
        location_lat=payload.location_lat,
        location_lng=payload.location_lng,
        location_name=payload.location_name,
        receipt_url=payload.receipt_url,
        expense_date=payload.expense_date,
        status=TicketStatus.PENDING,
        risk_level=RiskLevel.LOW,
    )

    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)

    return _ticket_to_response(ticket, driver.name, vehicle.registration_number)


@router.post("/{ticket_id}/action", response_model=TicketResponse)
async def approve_or_reject_ticket(
    ticket_id: int,
    payload: TicketApproval,
    uow = Depends(get_uow),
    event_service: OperationalEventService = Depends(get_event_service),
) -> TicketResponse:
    """
    Approve or reject a ticket.

    On approval:
    - Simulates a UPI payout (generates a mock transaction ID)
    - Phase 2 will send a WhatsApp confirmation to the driver

    On rejection:
    - Records the rejection reason
    - Phase 2 will notify the driver via WhatsApp
    """
    result = await db.execute(
        select(Ticket, Driver.name, Vehicle.registration_number)
        .join(Driver, Ticket.driver_id == Driver.id)
        .join(Vehicle, Ticket.vehicle_id == Vehicle.id)
        .where(Ticket.id == ticket_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, f"Ticket {ticket_id} not found")

    ticket, driver_name, truck_plate = row

    if ticket.status != TicketStatus.PENDING:
        raise HTTPException(400, f"Ticket already {ticket.status.value}")

    if payload.action == "approve":
        ticket.status = TicketStatus.APPROVED
        # Simulate UPI payout
        import uuid
        ticket.payout_reference = f"UPI-{uuid.uuid4().hex[:12].upper()}"
        
        # Flush here to get updated ticket state (though we don't strictly need it for the payload)
        await db.flush()
        
        # Emit an Unverified event for the new Expense Domain to pick up.
        # This bridges the legacy Ticket flow to the new Architecture.
        event_payload = OperationalEventCreate(
            entity_type=EntityType.EXPENSE,
            entity_id=f"TICKET-{ticket.id}",
            event_type=EventType.EXPENSE_RECORDED,
            capture_method=CaptureMethod.SYSTEM_INTERNAL,
            payload={
                "category": ticket.issue_type,
                "amount": ticket.amount,
                "currency": "INR",
                "description": ticket.description,
                "receipt_reference": ticket.receipt_url,
                "vehicle_id": ticket.vehicle_id,
                "driver_id": ticket.driver_id,
                "expense_date": ticket.expense_date.isoformat() if ticket.expense_date else None
            },
            notes=f"Auto-generated from approved Ticket {ticket.id}"
        )
        
        # This will save the event, and the validation engine will mark it VERIFIED, 
        # which dispatches it to the ProcessingEngine, which routes to ExpenseService.
        await event_service.create_event(event_payload)
        
    else:
        ticket.status = TicketStatus.REJECTED
        if payload.rejection_reason:
            existing_reasons = ticket.risk_reasons or ""
            ticket.risk_reasons = (
                f"{existing_reasons}\nRejected: {payload.rejection_reason}".strip()
            )

    await db.flush()
    await db.refresh(ticket)

    return _ticket_to_response(ticket, driver_name, truck_plate)
