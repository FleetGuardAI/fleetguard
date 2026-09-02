import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

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
    """Get all notifications for the current user's company."""
    # We get notifications for the user or the company broadly
    result = await db.execute(
        select(Notification)
        .where(Notification.company_id == current_user.company_id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.put("/api/v1/notifications/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark all notifications as read for the current company."""
    await db.execute(
        update(Notification)
        .where(Notification.company_id == current_user.company_id)
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
    """Mark a notification as read."""
    result = await db.execute(
        select(Notification)
        .where(
            Notification.id == notification_id,
            Notification.company_id == current_user.company_id
        )
    )
    notification = result.scalars().first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    notification.is_read = True
    await db.commit()
    
    return {"status": "success", "message": "Notification marked as read"}
