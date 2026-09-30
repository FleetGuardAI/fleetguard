from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime

from database import get_db
from models.admin_domain import AdminUser, AdminAuditLog
from models.document import Document, DocumentVerificationStatus
from models.notification import Notification, NotificationCategory
from services.admin_auth_service import require_admin_permission
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/admin/documents", tags=["Admin Documents"])

class DocumentResponse(BaseModel):
    id: str
    original_filename: str
    mime_type: str
    status: str
    verification_status: str
    uploaded_by: Optional[str] = None
    company_id: Optional[int] = None
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class VerificationRequest(BaseModel):
    reason: Optional[str] = None

@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    admin: AdminUser = Depends(require_admin_permission("support.view")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return result.scalars().all()

@router.post("/{doc_id}/approve", response_model=DocumentResponse)
async def approve_document(
    doc_id: str,
    admin: AdminUser = Depends(require_admin_permission("support.reply")),
    db: AsyncSession = Depends(get_db)
):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc.verification_status = DocumentVerificationStatus.APPROVED
    doc.verified_by = str(admin.id)
    doc.verified_at = datetime.utcnow()
    doc.rejection_reason = None
    
    audit = AdminAuditLog(
        admin_id=admin.id,
        action="DOCUMENT_APPROVED",
        resource_type="Document",
        resource_id=str(doc.id)
    )
    db.add(audit)
    
    if doc.company_id:
        notif = Notification(
            category=NotificationCategory.SYSTEM,
            title="Document Approved",
            description=f"Your document {doc.original_filename} has been approved.",
            company_id=doc.company_id
        )
        db.add(notif)
    
    await db.commit()
    await db.refresh(doc)
    return doc

@router.post("/{doc_id}/reject", response_model=DocumentResponse)
async def reject_document(
    doc_id: str,
    payload: VerificationRequest,
    admin: AdminUser = Depends(require_admin_permission("support.reply")),
    db: AsyncSession = Depends(get_db)
):
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc.verification_status = DocumentVerificationStatus.REJECTED
    doc.verified_by = str(admin.id)
    doc.verified_at = datetime.utcnow()
    doc.rejection_reason = payload.reason
    
    audit = AdminAuditLog(
        admin_id=admin.id,
        action="DOCUMENT_REJECTED",
        resource_type="Document",
        resource_id=str(doc.id),
        reason=payload.reason
    )
    db.add(audit)
    
    if doc.company_id:
        notif = Notification(
            category=NotificationCategory.SYSTEM,
            title="Document Rejected",
            description=f"Your document {doc.original_filename} was rejected. Reason: {payload.reason}",
            company_id=doc.company_id
        )
        db.add(notif)
    
    await db.commit()
    await db.refresh(doc)
    return doc
