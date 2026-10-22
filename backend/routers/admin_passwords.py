from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional
from datetime import datetime, timezone

from database import get_db
from models.admin_domain import AdminUser, AdminAuditLog
from models.support_domain import PasswordResetRequestAdmin, RequesterType
from models.user import User
from models.notification import Notification, NotificationCategory
from services.admin_auth_service import require_admin_permission
from pydantic import BaseModel, ConfigDict

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

    model_config = ConfigDict(from_attributes=True)

@router.get("", response_model=List[PasswordResetResponse])
@router.get("/", response_model=List[PasswordResetResponse])
async def list_password_resets(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, APPROVED, REJECTED)"),
    search: Optional[str] = Query(None, description="Search email or phone"),
    admin: AdminUser = Depends(require_admin_permission("support.view")),
    db: AsyncSession = Depends(get_db)
):
    """
    List password reset requests for Super Admin review.
    Supports no-trailing-slash endpoint to eliminate 307 redirect issues with frontend Axios.
    """
    query = select(PasswordResetRequestAdmin).order_by(PasswordResetRequestAdmin.created_at.desc())

    if status:
        query = query.where(PasswordResetRequestAdmin.status == status.upper())
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                PasswordResetRequestAdmin.requester_email_phone.ilike(term),
                PasswordResetRequestAdmin.reason.ilike(term)
            )
        )

    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{request_id}", response_model=PasswordResetResponse)
async def get_password_reset(
    request_id: int,
    admin: AdminUser = Depends(require_admin_permission("support.view")),
    db: AsyncSession = Depends(get_db)
):
    """Get single password reset request details."""
    req = await db.get(PasswordResetRequestAdmin, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return req

@router.post("/{request_id}/approve", response_model=PasswordResetResponse)
async def approve_password_reset(
    request_id: int,
    admin: AdminUser = Depends(require_admin_permission("support.reply")),
    db: AsyncSession = Depends(get_db)
):
    """
    Super Admin approves password reset request.
    Records audit log and sends in-app notification if user account exists.
    """
    req = await db.get(PasswordResetRequestAdmin, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        
    req.status = "APPROVED"
    req.resolved_by_id = admin.id
    req.updated_at = datetime.now(timezone.utc)
    
    audit = AdminAuditLog(
        admin_id=admin.id,
        action="PASSWORD_RESET_APPROVED",
        resource_type="PasswordResetRequestAdmin",
        resource_id=str(req.id),
        new_value="APPROVED"
    )
    db.add(audit)

    # Check if a user matches this identifier to deliver notification
    identifier = req.requester_email_phone.strip()
    user_query = select(User).where(or_(User.email == identifier, User.mobile_number == identifier))
    user_res = await db.execute(user_query)
    matched_user = user_res.scalar_one_or_none()
    if matched_user:
        notif = Notification(
            category=NotificationCategory.SYSTEM,
            title="Password Reset Request Approved",
            description="Your password reset request has been verified and approved by the Super Admin. You may proceed to set a new password.",
            is_read=False,
            company_id=matched_user.company_id,
            user_id=matched_user.id
        )
        db.add(notif)
    
    await db.commit()
    await db.refresh(req)
    return req

@router.post("/{request_id}/reject", response_model=PasswordResetResponse)
async def reject_password_reset(
    request_id: int,
    admin: AdminUser = Depends(require_admin_permission("support.reply")),
    db: AsyncSession = Depends(get_db)
):
    """
    Super Admin rejects password reset request.
    Records audit log and sends in-app notification if user account exists.
    """
    req = await db.get(PasswordResetRequestAdmin, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
        
    req.status = "REJECTED"
    req.resolved_by_id = admin.id
    req.updated_at = datetime.now(timezone.utc)
    
    audit = AdminAuditLog(
        admin_id=admin.id,
        action="PASSWORD_RESET_REJECTED",
        resource_type="PasswordResetRequestAdmin",
        resource_id=str(req.id),
        new_value="REJECTED"
    )
    db.add(audit)

    identifier = req.requester_email_phone.strip()
    user_query = select(User).where(or_(User.email == identifier, User.mobile_number == identifier))
    user_res = await db.execute(user_query)
    matched_user = user_res.scalar_one_or_none()
    if matched_user:
        notif = Notification(
            category=NotificationCategory.SYSTEM,
            title="Password Reset Request Rejected",
            description="Your password reset request could not be approved at this time. Please contact support if you need further assistance.",
            is_read=False,
            company_id=matched_user.company_id,
            user_id=matched_user.id
        )
        db.add(notif)
    
    await db.commit()
    await db.refresh(req)
    return req
