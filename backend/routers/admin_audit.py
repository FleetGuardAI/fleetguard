from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.admin_domain import AdminUser, AdminAuditLog
from services.admin_auth_service import require_admin_permission
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/admin/audit-logs", tags=["Admin Audit Logs"])

class AuditLogResponse(BaseModel):
    id: int
    admin_id: Optional[int] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip_address: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime
    actor_name: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[AuditLogResponse])
async def list_audit_logs(
    admin: AdminUser = Depends(require_admin_permission("dashboard.view")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(AdminAuditLog, AdminUser)
        .outerjoin(AdminUser, AdminAuditLog.admin_id == AdminUser.id)
        .order_by(AdminAuditLog.created_at.desc())
        .limit(100)
    )
    
    response = []
    for log, user in result.all():
        response.append({
            "id": log.id,
            "admin_id": log.admin_id,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "ip_address": log.ip_address,
            "reason": log.reason,
            "created_at": log.created_at,
            "actor_name": user.full_name if user else "System"
        })
        
    return response
