from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date

from database import get_db
from models.admin_domain import AdminUser, AdminAuditLog
from models.support_domain import SupportTicket, TicketStatus, PasswordResetRequestAdmin
from models.document import Document, DocumentVerificationStatus
from services.admin_auth_service import get_current_admin, require_admin_permission

router = APIRouter(prefix="/api/v1/admin/dashboard", tags=["Admin Dashboard"])

@router.get("/metrics")
async def get_dashboard_metrics(
    admin: AdminUser = Depends(require_admin_permission("dashboard.view")),
    db: AsyncSession = Depends(get_db)
):
    today = date.today()
    
    # 1. Open Tickets
    open_tickets_query = await db.execute(select(func.count()).where(SupportTicket.status == TicketStatus.OPEN))
    open_tickets = open_tickets_query.scalar() or 0
    
    # 2. Pending Verifications
    pending_docs_query = await db.execute(select(func.count()).where(Document.verification_status == DocumentVerificationStatus.PENDING))
    pending_docs = pending_docs_query.scalar() or 0
    
    # 3. Tickets Resolved Today
    resolved_today_query = await db.execute(
        select(func.count()).where(
            SupportTicket.status == TicketStatus.RESOLVED,
            func.date(SupportTicket.resolved_at) == today
        )
    )
    resolved_today = resolved_today_query.scalar() or 0
    
    # 4. Active Agents (SUPPORT_AGENT or OPERATIONS_ADMIN)
    from models.admin_domain import AdminRole, AdminRoleType
    active_agents_query = await db.execute(
        select(func.count()).select_from(AdminUser).join(AdminRole).where(
            AdminUser.is_active == True,
            AdminRole.name.in_([AdminRoleType.SUPPORT_AGENT, AdminRoleType.OPERATIONS_ADMIN])
        )
    )
    active_agents = active_agents_query.scalar() or 0

    return {
        "open_tickets": open_tickets,
        "pending_verifications": pending_docs,
        "resolved_today": resolved_today,
        "active_agents": active_agents
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
        .limit(10)
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
