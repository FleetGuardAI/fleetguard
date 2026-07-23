"""
Assignment Management Domain - Schemas
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from domain.assignment.models import AssignmentStatus, AssignmentType


class CreateAssignmentRequest(BaseModel):
    organization_id: uuid.UUID
    assignment_type: AssignmentType
    source_entity_id: str
    target_entity_id: str
    effective_from: Optional[datetime] = None
    created_by: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdateAssignmentRequest(BaseModel):
    metadata: Optional[Dict[str, Any]] = None


class AssignmentResponse(BaseModel):
    assignment_id: uuid.UUID
    organization_id: uuid.UUID
    assignment_type: AssignmentType
    source_entity_id: str
    target_entity_id: str
    status: AssignmentStatus
    effective_from: datetime
    effective_until: Optional[datetime] = None
    created_by: str
    created_at: datetime
    ended_at: Optional[datetime] = None
    metadata: Dict[str, Any]


class AssignmentSummaryResponse(BaseModel):
    assignment_id: uuid.UUID
    assignment_type: AssignmentType
    source_entity_id: str
    target_entity_id: str
    status: AssignmentStatus
    effective_from: datetime
