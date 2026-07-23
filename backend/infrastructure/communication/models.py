"""
Message Gateway Framework - Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class CommunicationType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    DOCUMENT = "DOCUMENT"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    SYSTEM = "SYSTEM"


class Attachment(BaseModel):
    """
    Immutable representation of an attachment received via a communication channel.
    Does NOT contain extracted document OCR/data; that is the responsibility
    of the Attachment Processing Framework.
    """
    attachment_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    filename: Optional[str] = None
    media_type: str
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    storage_uri: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class Communication(BaseModel):
    """
    Immutable, vendor-agnostic representation of an inbound communication.
    """
    message_id: str
    channel: str
    sender: str
    receiver: str
    timestamp: datetime
    message_type: CommunicationType
    text: Optional[str] = None
    attachments: List[Attachment] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class CommunicationProcessingStatus(str, Enum):
    SUCCESS = "SUCCESS"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NORMALIZATION_ERROR = "NORMALIZATION_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"


class CommunicationProcessingResult(BaseModel):
    """
    Result of a webhook passing through the Communication Gateway.
    """
    message: Optional[Communication] = None
    processing_status: CommunicationProcessingStatus
    error_message: Optional[str] = None
    execution_time: float
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
