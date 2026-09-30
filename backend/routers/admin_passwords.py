from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.admin_domain import AdminUser, AdminAuditLog
from models.support_domain import PasswordResetRequestAdmin, RequesterType
from services.admin_auth_service import require_admin_permission
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/admin/password-resets", tags=["Admin Password Resets"])

class PasswordResetResponse(BaseModel):
    id: int
    requester_type: str
    requester_email_phone: str
    reason: Optional[str] = None
    status: str
    ticket_id: Optional[int] = None
    resolved_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[PasswordResetResponse])
async def list_password_resets(
    admin: AdminUser = Depends(require_admin_permission("support.view")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(PasswordResetRequestAdmin).order_by(PasswordResetRequestAdmin.created_at.desc()))
    return result.scalars().all()

@router.post("/{request_id}/approve", response_model=PasswordResetResponse)
async def approve_password_reset(
    request_id: int,
    admin: AdminUser = Depends(require_admin_permission("support.reply")),
    db: AsyncSession = Depends(get_db)
):
    req = await db.get(PasswordResetRequestAdmin, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    req.status = "APPROVED"
    req.resolved_by_id = admin.id
    
    audit = AdminAuditLog(
        admin_id=admin.id,
        action="PASSWORD_RESET_APPROVED",
        resource_type="PasswordResetRequestAdmin",
        resource_id=str(req.id)
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(req)
    return req

@router.post("/{request_id}/reject", response_model=PasswordResetResponse)
async def reject_password_reset(
    request_id: int,
    admin: AdminUser = Depends(require_admin_permission("support.reply")),
    db: AsyncSession = Depends(get_db)
):
    req = await db.get(PasswordResetRequestAdmin, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    req.status = "REJECTED"
    req.resolved_by_id = admin.id
    
    audit = AdminAuditLog(
        admin_id=admin.id,
        action="PASSWORD_RESET_REJECTED",
        resource_type="PasswordResetRequestAdmin",
        resource_id=str(req.id)
    )
    db.add(audit)
    
    await db.commit()
    await db.refresh(req)
    return req
