"""
FleetGuard — Owner Emergency / SOS Router
Provides Owner Dashboard APIs to view and resolve active SOS alerts.
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.emergency import EmergencyAlert, EmergencyStatus
from routers.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/v1", tags=["Owner Emergency"])

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
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[int] = None
    resolution_notes: Optional[str] = None

    model_config = {"from_attributes": True}


@router.get("/sos/active", response_model=List[SosResponse])
async def list_active_sos(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List active emergency SOS alerts for fleet dashboard."""
    result = await db.execute(
        select(EmergencyAlert)
        .where(
            EmergencyAlert.company_id == current_user.company_id,
        )
        .order_by(desc(EmergencyAlert.created_at))
        .limit(limit)
    )
    alerts = result.scalars().all()
    return alerts


class ResolveRequest(BaseModel):
    notes: str


@router.post("/sos/{sos_id}/resolve", response_model=SosResponse)
async def resolve_sos(
    sos_id: int,
    payload: ResolveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resolve an emergency alert."""
    sos = await db.get(EmergencyAlert, sos_id)
    if not sos or sos.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    if sos.status != EmergencyStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alert is not active")

    sos.status = EmergencyStatus.RESOLVED
    sos.resolved_at = datetime.now(timezone.utc)
    sos.resolved_by = current_user.id
    sos.resolution_notes = payload.notes

    await db.commit()
    await db.refresh(sos)
    return sos
