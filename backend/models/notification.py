"""
FleetGuard — Notification ORM Model
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base


class NotificationCategory(str, enum.Enum):
    ALERT = "ALERT"
    TRIP = "TRIP"
    VEHICLE = "VEHICLE"
    FINANCE = "FINANCE"
    SYSTEM = "SYSTEM"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    category: Mapped[NotificationCategory] = mapped_column(
        Enum(NotificationCategory, native_enum=False, length=50), nullable=False, default=NotificationCategory.SYSTEM
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(1024), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, title='{self.title}', is_read={self.is_read})>"
