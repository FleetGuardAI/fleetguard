"""
Attachment Processing Framework - Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class AttachmentStatus(str, Enum):
    """
    Lifecycle tracking for an attachment passing through the framework.
    """
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    DUPLICATE = "DUPLICATE"
    ROUTED = "ROUTED"
    FAILED = "FAILED"


class Attachment(BaseModel):
    """
    Immutable enriched representation of an inbound attachment.
    """
    attachment_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    filename: Optional[str] = None
    media_type: str  # e.g., "image", "document", "audio", "video"
    mime_type: str   # e.g., "image/jpeg", "application/pdf"
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    storage_uri: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_channel: str
    uploader: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class AttachmentProcessingResult(BaseModel):
    """
    Result of processing an attachment.
    """
    attachment: Attachment
    processing_status: AttachmentStatus
    routed_processor: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: float
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
