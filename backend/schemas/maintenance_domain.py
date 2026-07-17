"""
FleetGuard — Maintenance Domain Pydantic Schemas
Defines value objects for maintenance operations and read-models for API responses.
"""

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from models.maintenance_domain import (
    MaintenanceStatus,
    MaintenanceCategory,
    TaskType,
    TaskStatus
)


# ===========================================================================
# Read Models
# ===========================================================================

class MaintenanceTaskResponse(BaseModel):
    id: int
    task_type: TaskType
    description: str
    status: TaskStatus
    notes: Optional[str] = None
    performed_at: Optional[datetime] = None
    
    origin_type: Optional[str] = None
    origin_id: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class MaintenanceRecordResponse(BaseModel):
    id: int
    business_id: str
    status: MaintenanceStatus
    category: MaintenanceCategory
    
    vehicle_id: Optional[int] = None
    
    workshop: Optional[str] = None
    service_provider: Optional[str] = None

    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None

    tasks: List[MaintenanceTaskResponse] = []

    origin_type: Optional[str] = None
    origin_id: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


# ===========================================================================
# Value Objects / Internal Commands
# ===========================================================================

class MaintenanceCreated(BaseModel):
    business_id: str
    category: Optional[MaintenanceCategory] = None
    vehicle_id: Optional[int] = None
    workshop: Optional[str] = None
    service_provider: Optional[str] = None


class MaintenanceScheduled(BaseModel):
    scheduled_date: datetime
    workshop: Optional[str] = None
    service_provider: Optional[str] = None


class MaintenanceStarted(BaseModel):
    pass


class MaintenanceCompleted(BaseModel):
    completed_date: datetime


class MaintenanceCancelled(BaseModel):
    pass


class MaintenanceTaskAdded(BaseModel):
    task_type: TaskType
    description: str
    notes: Optional[str] = None


class MaintenanceTaskCompleted(BaseModel):
    task_id: int
    status: TaskStatus
    performed_at: datetime
    notes: Optional[str] = None
