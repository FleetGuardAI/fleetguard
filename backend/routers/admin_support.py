from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from typing import List, Optional
from datetime import datetime, timezone, timedelta

from database import get_db
from models.admin_domain import AdminUser, AdminAuditLog
from models.support_domain import (
    SupportTicket,
    SupportTicketMessage,
    RequesterType,
    TicketCategory,
    TicketPriority,
    TicketStatus,
    MessageType,
)
from models.notification import Notification, NotificationCategory
from schemas.support_domain import (
    SupportTicketResponse,
    SupportTicketCreate,
    SupportTicketMessageResponse,
    SupportTicketMessageCreate,
    SupportTicketStatusUpdate,
    SupportTicketAssign,
)
from services.admin_auth_service import get_current_admin, require_admin_permission
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/admin/tickets", tags=["Admin Support"])


def _parse_ticket_lookup(ticket_id_str: str):
    try:
        return int(ticket_id_str), True
    except ValueError:
        return ticket_id_str, False


class PriorityUpdateRequest(BaseModel):
    priority: TicketPriority


@router.get("", response_model=List[SupportTicketResponse])
@router.get("/", response_model=List[SupportTicketResponse])
async def list_tickets(
    status: Optional[TicketStatus] = Query(None, description="Filter by status"),
    priority: Optional[TicketPriority] = Query(None, description="Filter by priority"),
    category: Optional[TicketCategory] = Query(None, description="Filter by category"),
    requester_type: Optional[RequesterType] = Query(None, description="Filter by requester type"),
    company_id: Optional[int] = Query(None, description="Filter by company"),
    search: Optional[str] = Query(None, description="Search ticket ID, title, or requester"),
    admin: AdminUser = Depends(require_admin_permission("support.view")),
    db: AsyncSession = Depends(get_db)
):
    """
    Super Admin ticket inbox:
    Lists tickets across ALL companies, tenants, drivers, and unassigned/system requests.
    Supports filtering and search.
    """
    query = select(SupportTicket).order_by(SupportTicket.created_at.desc())

    if status:
        query = query.where(SupportTicket.status == status)
    if priority:
        query = query.where(SupportTicket.priority == priority)
    if category:
        query = query.where(SupportTicket.category == category)
    if requester_type:
        query = query.where(SupportTicket.requester_type == requester_type)
    if company_id is not None:
        query = query.where(SupportTicket.company_id == company_id)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                SupportTicket.ticket_id.ilike(term),
                SupportTicket.title.ilike(term),
                SupportTicket.requester_name.ilike(term),
                SupportTicket.requester_email.ilike(term),
                SupportTicket.requester_phone.ilike(term),
            )
        )

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{ticket_id}", response_model=SupportTicketResponse)
async def get_ticket(
    ticket_id: str,
    admin: AdminUser = Depends(require_admin_permission("support.view")),
    db: AsyncSession = Depends(get_db)
):
    """Get ticket detail for Super Admin portal."""
    parsed_id, is_int = _parse_ticket_lookup(ticket_id)
    if is_int:
        query = select(SupportTicket).where(
            or_(SupportTicket.id == parsed_id, SupportTicket.ticket_id == ticket_id)
        )
    else:
        query = select(SupportTicket).where(SupportTicket.ticket_id == ticket_id)

    result = await db.execute(query)
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


@router.get("/{ticket_id}/messages", response_model=List[SupportTicketMessageResponse])
async def get_ticket_messages(
    ticket_id: str,
    admin: AdminUser = Depends(require_admin_permission("support.view")),
    db: AsyncSession = Depends(get_db)
):
    """
    Super Admin sees all messages: PUBLIC, INTERNAL_NOTE, and SYSTEM_EVENT.
    """
    parsed_id, is_int = _parse_ticket_lookup(ticket_id)
    if is_int:
        t_query = select(SupportTicket).where(
            or_(SupportTicket.id == parsed_id, SupportTicket.ticket_id == ticket_id)
        )
    else:
        t_query = select(SupportTicket).where(SupportTicket.ticket_id == ticket_id)

    t_res = await db.execute(t_query)
    ticket = t_res.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    result = await db.execute(
        select(SupportTicketMessage)
        .where(SupportTicketMessage.ticket_id == ticket.id)
        .order_by(SupportTicketMessage.created_at.asc())
    )
    return result.scalars().all()


@router.post("/{ticket_id}/messages", response_model=SupportTicketMessageResponse)
async def create_ticket_message(
    ticket_id: str,
    payload: SupportTicketMessageCreate,
    admin: AdminUser = Depends(require_admin_permission("support.reply")),
    db: AsyncSession = Depends(get_db)
):
    """
    Super Admin posts a reply (PUBLIC) or an INTERNAL_NOTE.
    If PUBLIC, creates user-facing notification and updates ticket status to WAITING_FOR_USER.
    """
    parsed_id, is_int = _parse_ticket_lookup(ticket_id)
    if is_int:
        t_query = select(SupportTicket).where(
            or_(SupportTicket.id == parsed_id, SupportTicket.ticket_id == ticket_id)
        )
    else:
        t_query = select(SupportTicket).where(SupportTicket.ticket_id == ticket_id)

    t_res = await db.execute(t_query)
    ticket = t_res.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    cleaned_content = payload.content.strip()
    if not cleaned_content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message content cannot be empty.")

    msg_type = payload.message_type or MessageType.PUBLIC
    now_utc = datetime.now(timezone.utc)
    recent_threshold = now_utc - timedelta(seconds=10)

    # 10-second idempotency check to prevent duplicate messages
    dup_q = (
        select(SupportTicketMessage)
        .where(
            SupportTicketMessage.ticket_id == ticket.id,
            SupportTicketMessage.content == cleaned_content,
            SupportTicketMessage.message_type == msg_type,
            SupportTicketMessage.sender_type == RequesterType.INTERNAL_USER,
            SupportTicketMessage.sender_id == admin.id,
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
        message_type=msg_type,
        sender_type=RequesterType.INTERNAL_USER,
        sender_id=admin.id,
        sender_name=admin.full_name or "Support Team",
    )
    db.add(message)

    # If public message, update status to WAITING_FOR_USER if currently OPEN or IN_PROGRESS
    if msg_type == MessageType.PUBLIC:
        if ticket.status in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS]:
            ticket.status = TicketStatus.WAITING_FOR_USER
        ticket.updated_at = datetime.now(timezone.utc)

        # Create user notification if company_id is present
        if ticket.company_id:
            user_notif = Notification(
                category=NotificationCategory.SYSTEM,
                title=f"New Support Reply on #{ticket.ticket_id}",
                description=f"Support agent {admin.full_name or 'Support'}: {payload.content[:100]}",
                is_read=False,
                company_id=ticket.company_id,
                user_id=ticket.requester_id if ticket.requester_type == RequesterType.FLEET_OWNER else None,
            )
            db.add(user_notif)

    # Log audit
    audit = AdminAuditLog(
        admin_id=admin.id,
        action="TICKET_REPLIED" if msg_type == MessageType.PUBLIC else "TICKET_INTERNAL_NOTE_ADDED",
        resource_type="SupportTicket",
        resource_id=str(ticket.id),
        new_value=f"Type: {msg_type.value}, Length: {len(payload.content)}"
    )
    db.add(audit)

    await db.commit()
    await db.refresh(message)
    return message


@router.patch("/{ticket_id}/status", response_model=SupportTicketResponse)
async def update_ticket_status(
    ticket_id: str,
    payload: SupportTicketStatusUpdate,
    admin: AdminUser = Depends(require_admin_permission("support.reply")),
    db: AsyncSession = Depends(get_db)
):
    """
    Super Admin changes ticket status (OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED).
    Updates timestamps, logs audit trail, records a system event message, and notifies tenant.
    """
    parsed_id, is_int = _parse_ticket_lookup(ticket_id)
    if is_int:
        t_query = select(SupportTicket).where(
            or_(SupportTicket.id == parsed_id, SupportTicket.ticket_id == ticket_id)
        )
    else:
        t_query = select(SupportTicket).where(SupportTicket.ticket_id == ticket_id)

    t_res = await db.execute(t_query)
    ticket = t_res.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    old_status = ticket.status
    new_status = payload.status
    ticket.status = new_status
    now = datetime.now(timezone.utc)
    ticket.updated_at = now

    if new_status == TicketStatus.RESOLVED and not ticket.resolved_at:
        ticket.resolved_at = now
    elif new_status == TicketStatus.CLOSED and not ticket.closed_at:
        ticket.closed_at = now
    elif new_status in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS]:
        # If reopened
        ticket.closed_at = None

    # System message recording status transition
    sys_msg = SupportTicketMessage(
        ticket_id=ticket.id,
        content=f"Status changed from {old_status.value} to {new_status.value} by {admin.full_name or 'Super Admin'}"
                + (f" (Note: {payload.internal_note})" if payload.internal_note else ""),
        message_type=MessageType.SYSTEM_EVENT,
        sender_type=RequesterType.INTERNAL_USER,
        sender_id=admin.id,
        sender_name="System",
    )
    db.add(sys_msg)

    # Log audit
    audit = AdminAuditLog(
        admin_id=admin.id,
        action="TICKET_STATUS_UPDATED",
        resource_type="SupportTicket",
        resource_id=str(ticket.id),
        old_value=old_status.value,
        new_value=new_status.value,
        reason=payload.internal_note,
    )
    db.add(audit)

    # Notify tenant
    if ticket.company_id:
        user_notif = Notification(
            category=NotificationCategory.SYSTEM,
            title=f"Support Ticket #{ticket.ticket_id} {new_status.value.replace('_', ' ').title()}",
            description=f"Your ticket '{ticket.title}' is now {new_status.value.replace('_', ' ').lower()}.",
            is_read=False,
            company_id=ticket.company_id,
            user_id=ticket.requester_id if ticket.requester_type == RequesterType.FLEET_OWNER else None,
        )
        db.add(user_notif)

    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.patch("/{ticket_id}/assign", response_model=SupportTicketResponse)
async def assign_ticket_agent(
    ticket_id: str,
    payload: SupportTicketAssign,
    admin: AdminUser = Depends(require_admin_permission("support.reply")),
    db: AsyncSession = Depends(get_db)
):
    """Assign or re-assign ticket to an admin agent."""
    parsed_id, is_int = _parse_ticket_lookup(ticket_id)
    if is_int:
        t_query = select(SupportTicket).where(
            or_(SupportTicket.id == parsed_id, SupportTicket.ticket_id == ticket_id)
        )
    else:
        t_query = select(SupportTicket).where(SupportTicket.ticket_id == ticket_id)

    t_res = await db.execute(t_query)
    ticket = t_res.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    old_agent = ticket.assigned_agent_id
    ticket.assigned_agent_id = payload.assigned_agent_id
    ticket.updated_at = datetime.now(timezone.utc)

    audit = AdminAuditLog(
        admin_id=admin.id,
        action="TICKET_ASSIGNED",
        resource_type="SupportTicket",
        resource_id=str(ticket.id),
        old_value=str(old_agent) if old_agent else None,
        new_value=str(payload.assigned_agent_id) if payload.assigned_agent_id else None,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.patch("/{ticket_id}/priority", response_model=SupportTicketResponse)
async def update_ticket_priority(
    ticket_id: str,
    payload: PriorityUpdateRequest,
    admin: AdminUser = Depends(require_admin_permission("support.reply")),
    db: AsyncSession = Depends(get_db)
):
    """Update ticket priority."""
    parsed_id, is_int = _parse_ticket_lookup(ticket_id)
    if is_int:
        t_query = select(SupportTicket).where(
            or_(SupportTicket.id == parsed_id, SupportTicket.ticket_id == ticket_id)
        )
    else:
        t_query = select(SupportTicket).where(SupportTicket.ticket_id == ticket_id)

    t_res = await db.execute(t_query)
    ticket = t_res.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    old_priority = ticket.priority
    ticket.priority = payload.priority
    ticket.updated_at = datetime.now(timezone.utc)

    audit = AdminAuditLog(
        admin_id=admin.id,
        action="TICKET_PRIORITY_UPDATED",
        resource_type="SupportTicket",
        resource_id=str(ticket.id),
        old_value=old_priority.value,
        new_value=payload.priority.value,
    )
    db.add(audit)

    await db.commit()
    await db.refresh(ticket)
    return ticket
