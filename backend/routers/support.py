from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from database import get_db
from models.user import User
from models.support_domain import SupportTicket, SupportTicketMessage, RequesterType, TicketCategory, TicketPriority, TicketStatus
from schemas.support_domain import SupportTicketResponse, SupportTicketCreate
from services.auth_service import get_current_user

router = APIRouter(prefix="/support", tags=["Owner Support"])

@router.post("/tickets", response_model=SupportTicketResponse, status_code=201)
async def create_support_ticket(
    payload: SupportTicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = SupportTicket(
        ticket_id=f"TICK-{uuid.uuid4().hex[:8].upper()}",
        title=payload.title,
        description=payload.description,
        category=payload.category,
        priority=payload.priority or TicketPriority.MEDIUM,
        status=TicketStatus.OPEN,
        requester_type=RequesterType.FLEET_OWNER,
        requester_id=current_user.id,
        requester_name=current_user.full_name,
        requester_email=current_user.email,
        company_id=current_user.company_id
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket

@router.get("/tickets", response_model=List[SupportTicketResponse])
async def list_support_tickets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(SupportTicket)
        .where(SupportTicket.company_id == current_user.company_id)
        .order_by(SupportTicket.created_at.desc())
    )
    return result.scalars().all()
