"""
Assignment Management Domain - Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from domain.assignment.value_objects import AssignmentId, AssignmentPeriod


class AssignmentType(str, Enum):
    DRIVER_TO_VEHICLE = "DRIVER_TO_VEHICLE"


class AssignmentStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ENDED = "ENDED"


class Assignment(BaseModel):
    """
    Immutable representation of an Assignment entity.
    Mutable state transitions should be done via creating a new copy.
    """
    assignment_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    organization_id: uuid.UUID
    assignment_type: AssignmentType
    source_entity_id: str
    target_entity_id: str
    status: AssignmentStatus = AssignmentStatus.PENDING
    
    # Using temporal values directly for easier querying/updating, though they correspond to AssignmentPeriod
    effective_from: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    effective_until: Optional[datetime] = None
    
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True, "extra": "forbid"}
