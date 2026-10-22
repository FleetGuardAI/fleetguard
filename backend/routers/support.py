from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import uuid

from database import get_db
from models.user import User
from models.support_domain import (
    SupportTicket,
    SupportTicketMessage,
    RequesterType,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    MessageType,
)
from schemas.support_domain import (
    SupportTicketResponse,
    SupportTicketCreate,
    SupportTicketMessageResponse,
    SupportTicketMessageCreate,
)
from services.auth_service import get_current_user

router = APIRouter(prefix="/support", tags=["Owner Support"])


def _parse_ticket_lookup(ticket_id_str: str):
    """Helper to check if ticket lookup is an integer id or string code (e.g. TICK-XXXX or SOS-XXXX)."""
    try:
        return int(ticket_id_str), True
    except ValueError:
        return ticket_id_str, False


@router.post("/tickets", response_model=SupportTicketResponse, status_code=status.HTTP_201_CREATED)
async def create_support_ticket(
    payload: SupportTicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new support ticket on behalf of the authenticated fleet owner/user.
    Guarantees tenant isolation by associating with current_user.company_id.
    """
    ticket_code = f"TICK-{uuid.uuid4().hex[:8].upper()}"
    ticket = SupportTicket(
        ticket_id=ticket_code,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        priority=payload.priority or TicketPriority.MEDIUM,
        status=TicketStatus.OPEN,
        requester_type=RequesterType.FLEET_OWNER,
        requester_id=current_user.id,
        requester_name=current_user.full_name,
        requester_email=current_user.email,
        requester_phone=current_user.mobile_number,
        company_id=current_user.company_id,
        driver_id=payload.driver_id,
        vehicle_id=payload.vehicle_id,
        trip_id=payload.trip_id,
    )
    db.add(ticket)
    await db.flush()  # assign ticket.id

    # Create initial public message in conversation thread
    initial_message = SupportTicketMessage(
        ticket_id=ticket.id,
        content=payload.description,
        message_type=MessageType.PUBLIC,
        sender_type=RequesterType.FLEET_OWNER,
        sender_id=current_user.id,
        sender_name=current_user.full_name,
    )
    db.add(initial_message)

    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/tickets", response_model=List[SupportTicketResponse])
async def list_support_tickets(
    status: Optional[TicketStatus] = Query(None, description="Filter by ticket status"),
    category: Optional[TicketCategory] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all tickets for the authenticated tenant company.
    Strictly scoped to current_user.company_id.
    """
    query = (
        select(SupportTicket)
        .where(SupportTicket.company_id == current_user.company_id)
        .order_by(SupportTicket.created_at.desc())
    )

    if status:
        query = query.where(SupportTicket.status == status)
    if category:
        query = query.where(SupportTicket.category == category)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def get_support_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed support ticket.
    Supports either integer ID or string ticket code (e.g. TICK-ABCDEF12).
    Enforces multi-tenant isolation.
    """
    parsed_id, is_int = _parse_ticket_lookup(ticket_id)
    if is_int:
        query = select(SupportTicket).where(
            or_(SupportTicket.id == parsed_id, SupportTicket.ticket_id == ticket_id),
            SupportTicket.company_id == current_user.company_id
        )
    else:
        query = select(SupportTicket).where(
            SupportTicket.ticket_id == ticket_id,
            SupportTicket.company_id == current_user.company_id
        )

    result = await db.execute(query)
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found"
        )
    return ticket


@router.get("/tickets/{ticket_id}/messages", response_model=List[SupportTicketMessageResponse])
async def get_ticket_messages(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List conversation messages for a ticket.
    SECURITY: Strips internal admin notes (INTERNAL_NOTE) — only returns PUBLIC messages to users.
    """
    parsed_id, is_int = _parse_ticket_lookup(ticket_id)
    if is_int:
        ticket_query = select(SupportTicket).where(
            or_(SupportTicket.id == parsed_id, SupportTicket.ticket_id == ticket_id),
            SupportTicket.company_id == current_user.company_id
        )
    else:
        ticket_query = select(SupportTicket).where(
            SupportTicket.ticket_id == ticket_id,
            SupportTicket.company_id == current_user.company_id
        )

    ticket_result = await db.execute(ticket_query)
    ticket = ticket_result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found"
        )

    # Only return PUBLIC messages to customer
    messages_query = (
        select(SupportTicketMessage)
        .where(
            SupportTicketMessage.ticket_id == ticket.id,
            SupportTicketMessage.message_type == MessageType.PUBLIC
        )
        .order_by(SupportTicketMessage.created_at.asc())
    )
    result = await db.execute(messages_query)
    return result.scalars().all()


@router.post("/tickets/{ticket_id}/messages", response_model=SupportTicketMessageResponse, status_code=status.HTTP_201_CREATED)
async def send_ticket_message(
    ticket_id: str,
    payload: SupportTicketMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fleet owner posts a reply to an existing support ticket.
    Forces message_type to PUBLIC.
    If ticket was RESOLVED or WAITING_FOR_USER, transitions back to IN_PROGRESS.
    """
    parsed_id, is_int = _parse_ticket_lookup(ticket_id)
    if is_int:
        ticket_query = select(SupportTicket).where(
            or_(SupportTicket.id == parsed_id, SupportTicket.ticket_id == ticket_id),
            SupportTicket.company_id == current_user.company_id
        )
    else:
        ticket_query = select(SupportTicket).where(
            SupportTicket.ticket_id == ticket_id,
            SupportTicket.company_id == current_user.company_id
        )

    ticket_result = await db.execute(ticket_query)
    ticket = ticket_result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Support ticket not found"
        )

    if ticket.status == TicketStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This support ticket has been closed. Please raise a new ticket."
        )

    cleaned_content = payload.content.strip()
    if not cleaned_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty."
        )

    now_utc = datetime.now(timezone.utc)
    recent_threshold = now_utc - timedelta(seconds=10)

    # 10-second idempotency check to prevent duplicate messages
    dup_q = (
        select(SupportTicketMessage)
        .where(
            SupportTicketMessage.ticket_id == ticket.id,
            SupportTicketMessage.content == cleaned_content,
            SupportTicketMessage.message_type == MessageType.PUBLIC,
            SupportTicketMessage.sender_type == RequesterType.FLEET_OWNER,
            SupportTicketMessage.sender_id == current_user.id,
            SupportTicketMessage.created_at >= recent_threshold,
        )
        .order_by(SupportTicketMessage.id.desc())
    )
    dup_res = await db.execute(dup_q)
    existing_message = dup_res.scalar_one_or_none()
    if existing_message:
        return existing_message

    message = SupportTicketMessage(
        ticket_id=ticket.id,
        content=cleaned_content,
        message_type=MessageType.PUBLIC,
        sender_type=RequesterType.FLEET_OWNER,
        sender_id=current_user.id,
        sender_name=current_user.full_name,
    )
    db.add(message)

    # Re-open or keep in progress if awaiting action
    if ticket.status in [TicketStatus.WAITING_FOR_USER, TicketStatus.RESOLVED]:
        ticket.status = TicketStatus.IN_PROGRESS
    ticket.updated_at = now_utc

    await db.commit()
    await db.refresh(message)
    return message
