import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import get_db
from models.admin_domain import AdminAuditLog, AdminUser
from models.notification import Notification, NotificationCategory
from models.password_reset_token import PasswordResetToken
from models.support_domain import PasswordResetRequestAdmin, RequesterType
from models.user import User
from services.admin_auth_service import require_admin_permission
from services.auth_service import _hash_token

router = APIRouter(prefix="/api/v1/admin/password-resets", tags=["Admin Password Resets"])


class PasswordResetResponse(BaseModel):
    id: int
    requester_type: str
    requester_email_phone: str
    reason: Optional[str] = None
    status: str
    ticket_id: Optional[int] = None
    resolved_by_id: Optional[int] = None
    user_id: Optional[int] = None
    token_issued_at: Optional[datetime] = None
    token_expires_at: Optional[datetime] = None
    token_used_at: Optional[datetime] = None
    token_revoked_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PasswordResetApproveResponse(PasswordResetResponse):
    reset_token: str
    expires_at: datetime
    instructions: str = (
        "Copy this unique token and email it to the user. This plaintext token is shown only once and will not be displayed again."
    )


class RejectPasswordResetRequest(BaseModel):
    reason: Optional[str] = None


@router.get("", response_model=List[PasswordResetResponse])
@router.get("/", response_model=List[PasswordResetResponse])
async def list_password_resets(
    status: Optional[str] = Query(None, description="Filter by status (PENDING, APPROVED, REJECTED, COMPLETED)"),
    search: Optional[str] = Query(None, description="Search email, phone, or request ID"),
    admin: AdminUser = Depends(require_admin_permission("support.view")),
    db: AsyncSession = Depends(get_db)
):
    """
    List password reset requests for Super Admin review.
    Tokens and token hashes are never exposed in listing endpoints.
    """
    query = select(PasswordResetRequestAdmin).order_by(PasswordResetRequestAdmin.created_at.desc())

    if status and status.strip():
        query = query.where(PasswordResetRequestAdmin.status == status.strip().upper())

    if search and search.strip():
        term = search.strip()
        search_filter = or_(
            PasswordResetRequestAdmin.requester_email_phone.ilike(f"%{term}%"),
            PasswordResetRequestAdmin.reason.ilike(f"%{term}%")
        )
        clean_num = term.lstrip("#")
        if clean_num.isdigit():
            search_filter = or_(search_filter, PasswordResetRequestAdmin.id == int(clean_num))
        query = query.where(search_filter)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{request_id}", response_model=PasswordResetResponse)
@router.get("/{request_id}/", response_model=PasswordResetResponse)
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


@router.post("/{request_id}/approve", response_model=PasswordResetApproveResponse)
@router.post("/{request_id}/approve/", response_model=PasswordResetApproveResponse)
async def approve_password_reset(
    request_id: int,
    admin: AdminUser = Depends(require_admin_permission("support.reply")),
    db: AsyncSession = Depends(get_db)
):
    """
    Super Admin approves a pending password reset request.
    Generates a cryptographically secure token, stores only its SHA-256 hash,
    and returns the plaintext token EXACTLY ONCE to the authorized Super Admin.
    """
    req = await db.get(PasswordResetRequestAdmin, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if req.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve request with status '{req.status}'. Only PENDING requests can be approved."
        )

    # Resolve matching user account
    user = None
    if req.user_id:
        user = await db.get(User, req.user_id)
    if not user:
        identifier = req.requester_email_phone.strip()
        user_query = select(User).where(
            or_(User.email.ilike(identifier), User.mobile_number == identifier)
        )
        user_res = await db.execute(user_query)
        user = user_res.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot approve request: No active user account found matching this identifier."
        )

    now_utc = datetime.now(timezone.utc)
    raw_token = secrets.token_urlsafe(36)
    tok_hash = _hash_token(raw_token)
    expires_at = now_utc + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)

    # Associate with request and user
    req.user_id = user.id
    req.status = "APPROVED"
    req.resolved_by_id = admin.id
    req.token_hash = tok_hash
    req.token_issued_at = now_utc
    req.token_expires_at = expires_at
    req.token_used_at = None
    req.token_revoked_at = None
    req.updated_at = now_utc

    # Invalidate prior active reset tokens for this user
    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None)
        )
        .values(used_at=now_utc)
    )

    # Insert into password_reset_tokens
    reset_entry = PasswordResetToken(
        user_id=user.id,
        company_id=user.company_id,
        token_hash=tok_hash,
        requested_identifier=req.requester_email_phone.strip(),
        expires_at=expires_at,
        reset_request_id=req.id,
    )
    db.add(reset_entry)

    # In-app notification for the user
    notif = Notification(
        category=NotificationCategory.SYSTEM,
        title="Password Reset Request Approved",
        description="Your password reset request has been verified and approved by the Super Admin. Please use the reset token provided by your administrator.",
        is_read=False,
        company_id=user.company_id,
        user_id=user.id
    )
    db.add(notif)

    # Audit log (token itself is NEVER logged)
    audit = AdminAuditLog(
        admin_id=admin.id,
        action="PASSWORD_RESET_APPROVED",
        resource_type="PasswordResetRequestAdmin",
        resource_id=str(req.id),
        new_value=f"APPROVED (expires_at={expires_at.isoformat()})"
    )
    db.add(audit)

    await db.commit()
    await db.refresh(req)

    return PasswordResetApproveResponse(
        id=req.id,
        requester_type=req.requester_type.value if hasattr(req.requester_type, 'value') else str(req.requester_type),
        requester_email_phone=req.requester_email_phone,
        reason=req.reason,
        status=req.status,
        ticket_id=req.ticket_id,
        resolved_by_id=req.resolved_by_id,
        user_id=req.user_id,
        token_issued_at=req.token_issued_at,
        token_expires_at=req.token_expires_at,
        token_used_at=req.token_used_at,
        token_revoked_at=req.token_revoked_at,
        rejection_reason=req.rejection_reason,
        created_at=req.created_at,
        updated_at=req.updated_at,
        reset_token=raw_token,
        expires_at=expires_at,
    )


@router.post("/{request_id}/reject", response_model=PasswordResetResponse)
@router.post("/{request_id}/reject/", response_model=PasswordResetResponse)
async def reject_password_reset(
    request_id: int,
    payload: Optional[RejectPasswordResetRequest] = None,
    admin: AdminUser = Depends(require_admin_permission("support.reply")),
    db: AsyncSession = Depends(get_db)
):
    """
    Super Admin rejects a pending password reset request.
    Records rejection reason, updates audit log, and notifies the user.
    """
    req = await db.get(PasswordResetRequestAdmin, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if req.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject request with status '{req.status}'. Only PENDING requests can be rejected."
        )

    now_utc = datetime.now(timezone.utc)
    req.status = "REJECTED"
    req.resolved_by_id = admin.id
    req.rejection_reason = payload.reason if payload and payload.reason else "Request rejected by administrator"
    req.updated_at = now_utc

    audit = AdminAuditLog(
        admin_id=admin.id,
        action="PASSWORD_RESET_REJECTED",
        resource_type="PasswordResetRequestAdmin",
        resource_id=str(req.id),
        new_value=f"REJECTED (reason={req.rejection_reason})"
    )
    db.add(audit)

    # Check if a user matches this identifier to notify
    identifier = req.requester_email_phone.strip()
    user_query = select(User).where(or_(User.email.ilike(identifier), User.mobile_number == identifier))
    user_res = await db.execute(user_query)
    matched_user = user_res.scalar_one_or_none()
    if matched_user:
        notif = Notification(
            category=NotificationCategory.SYSTEM,
            title="Password Reset Request Rejected",
            description=f"Your password reset request could not be approved at this time: {req.rejection_reason}",
            is_read=False,
            company_id=matched_user.company_id,
            user_id=matched_user.id
        )
        db.add(notif)

    await db.commit()
    await db.refresh(req)
    return req


@router.post("/{request_id}/reissue", response_model=PasswordResetApproveResponse)
@router.post("/{request_id}/reissue/", response_model=PasswordResetApproveResponse)
async def reissue_password_reset_token(
    request_id: int,
    admin: AdminUser = Depends(require_admin_permission("support.reply")),
    db: AsyncSession = Depends(get_db)
):
    """
    Secure revoke-and-regenerate workflow:
    If the plaintext token was lost after one-time display, revokes existing tokens
    and generates a brand new token for an approved reset request.
    """
    req = await db.get(PasswordResetRequestAdmin, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if req.status != "APPROVED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reissue token for request with status '{req.status}'. Only APPROVED requests can be reissued."
        )

    # Check user account
    user = None
    if req.user_id:
        user = await db.get(User, req.user_id)
    if not user:
        identifier = req.requester_email_phone.strip()
        user_query = select(User).where(
            or_(User.email.ilike(identifier), User.mobile_number == identifier)
        )
        user_res = await db.execute(user_query)
        user = user_res.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reissue: User account is no longer active."
        )

    now_utc = datetime.now(timezone.utc)

    # 1. Invalidate previous tokens
    req.token_revoked_at = now_utc
    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None)
        )
        .values(used_at=now_utc)
    )

    # 2. Generate brand new token
    raw_token = secrets.token_urlsafe(36)
    tok_hash = _hash_token(raw_token)
    expires_at = now_utc + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)

    req.token_hash = tok_hash
    req.token_issued_at = now_utc
    req.token_expires_at = expires_at
    req.token_revoked_at = None
    req.token_used_at = None
    req.updated_at = now_utc

    new_token_entry = PasswordResetToken(
        user_id=user.id,
        company_id=user.company_id,
        token_hash=tok_hash,
        requested_identifier=req.requester_email_phone.strip(),
        expires_at=expires_at,
        reset_request_id=req.id,
    )
    db.add(new_token_entry)

    audit = AdminAuditLog(
        admin_id=admin.id,
        action="PASSWORD_RESET_TOKEN_REISSUED",
        resource_type="PasswordResetRequestAdmin",
        resource_id=str(req.id),
        new_value=f"REISSUED (expires_at={expires_at.isoformat()})"
    )
    db.add(audit)

    await db.commit()
    await db.refresh(req)

    return PasswordResetApproveResponse(
        id=req.id,
        requester_type=req.requester_type.value if hasattr(req.requester_type, 'value') else str(req.requester_type),
        requester_email_phone=req.requester_email_phone,
        reason=req.reason,
        status=req.status,
        ticket_id=req.ticket_id,
        resolved_by_id=req.resolved_by_id,
        user_id=req.user_id,
        token_issued_at=req.token_issued_at,
        token_expires_at=req.token_expires_at,
        token_used_at=req.token_used_at,
        token_revoked_at=req.token_revoked_at,
        rejection_reason=req.rejection_reason,
        created_at=req.created_at,
        updated_at=req.updated_at,
        reset_token=raw_token,
        expires_at=expires_at,
        instructions="New reset token successfully issued. Previous tokens have been revoked. Securely email this token to the user."
    )
