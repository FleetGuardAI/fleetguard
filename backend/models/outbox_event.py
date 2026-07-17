"""
FleetGuard — Outbox Event Model
Implements the Transactional Outbox Pattern to guarantee at-least-once delivery
of Operational Events to Kafka without distributed transactions.
"""

from typing import Any, Optional
from datetime import datetime
import enum

from sqlalchemy import Integer, String, DateTime, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base


class OutboxStatus(str, enum.Enum):
    PENDING = "PENDING"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    # Note: No FAILED status. Transient errors just increase retry_count and remain PENDING.
    # DLQ/Failed state will be introduced in a future epic.


class OutboxEvent(Base):
    """
    Represents an event staged for publishing to Kafka.
    """
    __tablename__ = "outbox_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Optional correlation ID. Typically the operational_event_id.
    event_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)
    
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    headers: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    status: Mapped[OutboxStatus] = mapped_column(Enum(OutboxStatus), default=OutboxStatus.PENDING, index=True, nullable=False)
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Retry mechanics
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
