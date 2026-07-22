"""
Notification Service - Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class NotificationPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DeliveryStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


class NotificationChannel(str, Enum):
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"
    SMS = "SMS"
    WEBHOOK = "WEBHOOK"


class Notification(BaseModel):
    """
    Immutable representation of a notification intent.
    """
    notification_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    recipient: str
    channels: List[NotificationChannel]
    subject: Optional[str] = None
    message: str
    priority: NotificationPriority = NotificationPriority.NORMAL
    idempotency_key: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class DeliveryResult(BaseModel):
    """
    Immutable representation of a delivery attempt for a specific channel.
    """
    result_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    notification_id: uuid.UUID
    channel: NotificationChannel
    status: DeliveryStatus
    provider_reference: Optional[str] = None
    delivered_at: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
