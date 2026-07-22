"""
Assignment Management Domain - Events
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = {"frozen": True}


class AssignmentCreated(DomainEvent):
    assignment_id: uuid.UUID
    organization_id: uuid.UUID
    assignment_type: str
    source_entity_id: str
    target_entity_id: str
    effective_from: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AssignmentActivated(DomainEvent):
    assignment_id: uuid.UUID
    reason: Optional[str] = None


class AssignmentSuspended(DomainEvent):
    assignment_id: uuid.UUID
    reason: Optional[str] = None


class AssignmentEnded(DomainEvent):
    assignment_id: uuid.UUID
    ended_at: datetime
    reason: Optional[str] = None


class AssignmentTransferred(DomainEvent):
    """
    Emitted when an assignment ends specifically because the source entity was transferred to a new target.
    """
    old_assignment_id: uuid.UUID
    new_assignment_id: uuid.UUID
    source_entity_id: str
    old_target_entity_id: str
    new_target_entity_id: str
    reason: Optional[str] = None
