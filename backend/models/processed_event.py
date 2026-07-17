"""
FleetGuard — Processed Event Model
Used by the Idempotency Framework to strictly enforce that a Business Domain
processes an Operational Event exactly once.
"""

from typing import Any, Optional
from datetime import datetime

from sqlalchemy import Integer, String, DateTime, JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base


class ProcessedEvent(Base):
    """
    Records the successful processing of an Operational Event by a specific Business Domain.
    Enforces a unique constraint to prevent duplicate processing.
    """
    __tablename__ = "processed_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    operational_event_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    domain_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processing_result: Mapped[str] = mapped_column(String(50), nullable=False)
    metadata_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("operational_event_id", "domain_name", name="uq_processed_event_domain"),
    )
