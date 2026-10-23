from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from datetime import datetime, date, time, timezone

from database import get_db
from models.admin_domain import AdminUser, AdminAuditLog, AdminRole, AdminRoleType
from models.support_domain import SupportTicket, TicketStatus, PasswordResetRequestAdmin
from models.document import Document, DocumentVerificationStatus
from services.admin_auth_service import require_admin_permission

router = APIRouter(prefix="/api/v1/admin/dashboard", tags=["Admin Dashboard"])

@router.get("/metrics")
async def get_dashboard_metrics(
    admin: AdminUser = Depends(require_admin_permission("dashboard.view")),
    db: AsyncSession = Depends(get_db)
):
    today_start = datetime.combine(date.today(), time.min).replace(tzinfo=timezone.utc)
    
    # 1. Open / Active Tickets (OPEN, IN_PROGRESS, WAITING_FOR_USER, REOPENED)
    open_tickets_query = await db.execute(
        select(func.count()).where(
            SupportTicket.status.in_([
                TicketStatus.OPEN,
                TicketStatus.IN_PROGRESS,
                TicketStatus.WAITING_FOR_USER,
                TicketStatus.REOPENED
            ])
        )
    )
    open_tickets = open_tickets_query.scalar() or 0
    
    # 2. Pending Document Verifications
    pending_docs_query = await db.execute(
        select(func.count()).where(Document.verification_status == DocumentVerificationStatus.PENDING)
    )
    pending_docs = pending_docs_query.scalar() or 0
    
    # 3. Tickets Resolved Today
    resolved_today_query = await db.execute(
        select(func.count()).where(
            SupportTicket.status.in_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
            or_(
                SupportTicket.resolved_at >= today_start,
                SupportTicket.closed_at >= today_start
            )
        )
    )
    resolved_today = resolved_today_query.scalar() or 0
    
    # 4. Active Agents (SUPPORT_AGENT or OPERATIONS_ADMIN)
    active_agents_query = await db.execute(
        select(func.count()).select_from(AdminUser).join(AdminRole).where(
            AdminUser.is_active == True,
            AdminRole.name.in_([AdminRoleType.SUPPORT_AGENT, AdminRoleType.OPERATIONS_ADMIN])
        )
    )
    active_agents = active_agents_query.scalar() or 0

    # 5. Pending Password Reset Requests
    pending_resets_query = await db.execute(
        select(func.count()).where(PasswordResetRequestAdmin.status == "PENDING")
    )
    pending_password_resets = pending_resets_query.scalar() or 0

    return {
        "open_tickets": open_tickets,
        "pending_verifications": pending_docs,
        "resolved_today": resolved_today,
        "active_agents": active_agents,
        "pending_password_resets": pending_password_resets,
    }

@router.get("/recent-activity")
async def get_recent_activity(
    admin: AdminUser = Depends(require_admin_permission("dashboard.view")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AdminAuditLog, AdminUser)
        .outerjoin(AdminUser, AdminAuditLog.admin_id == AdminUser.id)
        .order_by(AdminAuditLog.created_at.desc())
        .limit(15)
    )
    rows = result.all()
    
    activities = []
    for log, user in rows:
        activities.append({
            "id": log.id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "timestamp": log.created_at,
            "actor_name": user.full_name if user else "System",
            "actor_email": user.email if user else None,
        })
        
    return activities
