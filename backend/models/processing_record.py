"""
FleetGuard — Processing Record ORM Model
Tracks the lifecycle of an Operational Event through the Processing Engine.
"""

import enum
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Integer, String, Enum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from database import Base


class ProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProcessingRecord(Base):
    """
    Tracks the execution status of a single Operational Event as it is
    routed to the various Business Domains by the Processing Engine.
    """
    __tablename__ = "processing_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Event reference (String, not FK, to avoid tight coupling)
    event_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    
    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, name="processing_status"),
        nullable=False,
        default=ProcessingStatus.PENDING,
        index=True
    )
    
    # JSON list of domain names that were successfully invoked
    domains_invoked: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    
    # JSON list of {domain: str, error: str}
    domains_failed: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Elapsed time in milliseconds
    execution_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ProcessingRecord(event_id='{self.event_id}', status='{self.status.value}')>"
