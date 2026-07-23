"""
Assignment Management Domain - Value Objects
"""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AssignmentId(BaseModel):
    value: uuid.UUID = Field(default_factory=uuid.uuid4)
    
    model_config = {"frozen": True}
    
    def __str__(self) -> str:
        return str(self.value)


class AssignmentPeriod(BaseModel):
    """
    Represents the temporal bounds of an assignment.
    """
    effective_from: datetime
    effective_until: Optional[datetime] = None

    model_config = {"frozen": True}
    
    def is_active_at(self, dt: datetime) -> bool:
        if dt < self.effective_from:
            return False
        if self.effective_until and dt > self.effective_until:
            return False
        return True
