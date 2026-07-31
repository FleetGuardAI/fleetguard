"""
FleetGuard — Fleet Invite Router (Dashboard API)

Allows fleet managers / admins to generate and manage QR code invites for driver onboarding.
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from models.fleet_invite import FleetInvite
from services.auth_service import get_current_user

logger = logging.getLogger("fleetguard.fleet_invite")

router = APIRouter(prefix="/api/v1/fleet", tags=["Fleet Invites"])


class CreateInviteRequest(BaseModel):
    label: Optional[str] = "Fleet Join Invite"
    max_uses: Optional[int] = None
    expires_in_days: Optional[int] = 30


class FleetInviteResponse(BaseModel):
    id: int
    company_id: int
    invite_token: str
    label: Optional[str]
    is_active: bool
    max_uses: Optional[int]
    use_count: int
    created_at: datetime
    expires_at: Optional[datetime]
    qr_data: str

    model_config = {"from_attributes": True}


@router.post("/invite", response_model=FleetInviteResponse, status_code=status.HTTP_201_CREATED)
async def create_fleet_invite(
    payload: CreateInviteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new fleet invite token with QR code data.
    """
    token = f"fg_invite_{uuid.uuid4().hex}"
    expires_at = (
        datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)
        if payload.expires_in_days
        else None
    )

    invite = FleetInvite(
        company_id=current_user.company_id,
        invite_token=token,
        label=payload.label,
        is_active=True,
        max_uses=payload.max_uses,
        use_count=0,
        expires_at=expires_at,
    )

    db.add(invite)
    await db.commit()
    await db.refresh(invite)

    # QR payload string format
    qr_data = f"fleetguard://invite?token={token}&company={current_user.company_id}"

    return FleetInviteResponse(
        id=invite.id,
        company_id=invite.company_id,
        invite_token=invite.invite_token,
        label=invite.label,
        is_active=invite.is_active,
        max_uses=invite.max_uses,
        use_count=invite.use_count,
        created_at=invite.created_at,
        expires_at=invite.expires_at,
        qr_data=qr_data,
    )


@router.get("/invites", response_model=List[FleetInviteResponse])
async def list_fleet_invites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all invite QR codes for the active company."""
    result = await db.execute(
        select(FleetInvite).where(FleetInvite.company_id == current_user.company_id)
    )
    invites = result.scalars().all()

    return [
        FleetInviteResponse(
            id=inv.id,
            company_id=inv.company_id,
            invite_token=inv.invite_token,
            label=inv.label,
            is_active=inv.is_active,
            max_uses=inv.max_uses,
            use_count=inv.use_count,
            created_at=inv.created_at,
            expires_at=inv.expires_at,
            qr_data=f"fleetguard://invite?token={inv.invite_token}&company={inv.company_id}",
        )
        for inv in invites
    ]
