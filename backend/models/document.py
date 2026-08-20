"""
FleetGuard — Document Domain Model

Represents any physical or digital document uploaded to the platform
(e.g., fuel receipts, toll tickets, invoices, driver licenses).
Serves as the foundation for the Document Intelligence Pipeline.
"""

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import String, Enum, func
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class DocumentStorageStatus(str, enum.Enum):
    """
    Infrastructure lifecycle status of a stored document.
    """
    UPLOADED = "UPLOADED"       # Upload received, file in temp buffer
    STORED = "STORED"           # File saved to physical storage
    AVAILABLE = "AVAILABLE"     # File is accessible to other modules
    FAILED = "FAILED"           # Storage encountered an error


class Document(Base):
    """
    Domain model for all documents ingested into FleetGuard.
    """
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="The name of the file as uploaded by the user.",
    )
    
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="MIME type (e.g., image/jpeg, application/pdf).",
    )
    
    storage_path: Mapped[str] = mapped_column(
        String(1024),
        nullable=False,
        doc="Location of the physical file (local path or cloud URI).",
    )
    
    status: Mapped[DocumentStorageStatus] = mapped_column(
        Enum(DocumentStorageStatus, name="documentstoragestatus"),
        nullable=False,
        default=DocumentStorageStatus.UPLOADED,
        index=True,
    )
    
    uploaded_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="ID of the user or system that uploaded the document.",
    )
    
    company_id: Mapped[int | None] = mapped_column(
        nullable=True,
        index=True,
        doc="ID of the company that owns the document.",
    )
    
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} status={self.status.value}>"
