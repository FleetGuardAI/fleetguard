"""
Audit Framework - Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class AuditSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuditCategory(str, Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"
    DEVICE = "DEVICE"
    DOCUMENT = "DOCUMENT"
    CONFIGURATION = "CONFIGURATION"
    SCHEDULER = "SCHEDULER"
    NOTIFICATION = "NOTIFICATION"
    SECURITY = "SECURITY"
    UNKNOWN = "UNKNOWN"


class AuditEvent(BaseModel):
    audit_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    category: AuditCategory
    severity: AuditSeverity = AuditSeverity.INFO
    event_name: str
    entity_type: str
    entity_id: str
    actor_type: str
    actor_id: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class EntityChange(BaseModel):
    field_name: str
    previous_value: Any
    new_value: Any

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class AuditRecord(BaseModel):
    event: AuditEvent
    changes: List[EntityChange] = Field(default_factory=list)

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
