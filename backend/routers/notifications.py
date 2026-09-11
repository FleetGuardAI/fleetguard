import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_

from database import get_db
from models.user import User
from models.notification import Notification
from routers.auth import get_current_user
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Notifications"])

class NotificationResponse(BaseModel):
    id: int
    category: str
    title: str
    description: str
    is_read: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.get("/api/v1/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notifications for the current user.
    
    Returns:
    - Notifications targeted specifically at this user (user_id matches)
    - Company-wide notifications (user_id is NULL) for the user's company
    
    Company isolation is enforced: users can only see their own company's notifications.
    """
    result = await db.execute(
        select(Notification)
        .where(Notification.company_id == current_user.company_id)
        .where(
            or_(
                Notification.user_id == current_user.id,
                Notification.user_id.is_(None),
            )
        )
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.put("/api/v1/notifications/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark all visible notifications as read for the current user."""
    await db.execute(
        update(Notification)
        .where(Notification.company_id == current_user.company_id)
        .where(
            or_(
                Notification.user_id == current_user.id,
                Notification.user_id.is_(None),
            )
        )
        .values(is_read=True)
    )
    await db.commit()
    
    return {"status": "success", "message": "All notifications marked as read"}

@router.put("/api/v1/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a single notification as read. Enforces company and user ownership."""
    result = await db.execute(
        select(Notification)
        .where(
            Notification.id == notification_id,
            Notification.company_id == current_user.company_id,
            or_(
                Notification.user_id == current_user.id,
                Notification.user_id.is_(None),
            ),
        )
    )
    notification = result.scalars().first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notification.is_read = True
    await db.commit()
    
    return {"status": "success", "message": "Notification marked as read"}


@router.delete("/api/v1/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a single notification. Enforces company and user ownership.
    Only notifications visible to the current user can be deleted.
    """
    result = await db.execute(
        select(Notification)
        .where(
            Notification.id == notification_id,
            Notification.company_id == current_user.company_id,
            or_(
                Notification.user_id == current_user.id,
                Notification.user_id.is_(None),
            ),
        )
    )
    notification = result.scalars().first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    await db.delete(notification)
    await db.commit()

    return {"status": "success", "message": "Notification deleted"}
