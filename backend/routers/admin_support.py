from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from database import get_db
from models.admin_domain import AdminUser
from models.support_domain import SupportTicket, SupportTicketMessage
from schemas.support_domain import SupportTicketResponse, SupportTicketCreate, SupportTicketMessageResponse, SupportTicketMessageCreate
from services.admin_auth_service import get_current_admin, require_admin_permission

router = APIRouter(prefix="/api/v1/admin/tickets", tags=["Admin Support"])

@router.get("/", response_model=List[SupportTicketResponse])
async def list_tickets(
    admin: AdminUser = Depends(require_admin_permission("support.view")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(SupportTicket).order_by(SupportTicket.created_at.desc()))
    return result.scalars().all()

@router.get("/{ticket_id}", response_model=SupportTicketResponse)
async def get_ticket(
    ticket_id: int,
    admin: AdminUser = Depends(require_admin_permission("support.view")),
    db: AsyncSession = Depends(get_db)
):
    ticket = await db.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket

@router.get("/{ticket_id}/messages", response_model=List[SupportTicketMessageResponse])
async def get_ticket_messages(
    ticket_id: int,
    admin: AdminUser = Depends(require_admin_permission("support.view")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(SupportTicketMessage).where(SupportTicketMessage.ticket_id == ticket_id).order_by(SupportTicketMessage.created_at.asc()))
    return result.scalars().all()

@router.post("/{ticket_id}/messages", response_model=SupportTicketMessageResponse)
async def create_ticket_message(
    ticket_id: int,
    payload: SupportTicketMessageCreate,
    admin: AdminUser = Depends(require_admin_permission("support.reply")),
    db: AsyncSession = Depends(get_db)
):
    from models.support_domain import RequesterType
    ticket = await db.get(SupportTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
        
    message = SupportTicketMessage(
        ticket_id=ticket.id,
        content=payload.content,
        message_type=payload.message_type,
        sender_type=RequesterType.INTERNAL_USER,
        sender_id=admin.id,
        sender_name=admin.full_name
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message
