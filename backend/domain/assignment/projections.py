"""
Assignment Management Domain - Projections
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from domain.assignment.models import AssignmentStatus, AssignmentType


class AssignmentSummary(BaseModel):
    assignment_id: uuid.UUID
    assignment_type: AssignmentType
    source_entity_id: str
    target_entity_id: str
    status: AssignmentStatus
    effective_from: datetime
    effective_until: Optional[datetime] = None


class VehicleAssignmentSummary(BaseModel):
    vehicle_id: str
    active_driver_id: Optional[str] = None
    assignment_id: Optional[uuid.UUID] = None
    effective_from: Optional[datetime] = None


class DriverAssignmentSummary(BaseModel):
    driver_id: str
    active_vehicle_id: Optional[str] = None
    assignment_id: Optional[uuid.UUID] = None
    effective_from: Optional[datetime] = None
