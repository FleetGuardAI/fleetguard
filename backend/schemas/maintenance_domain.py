"""
FleetGuard — Maintenance Domain Pydantic Schemas
Defines value objects for maintenance operations and read-models for API responses.
"""

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import uuid

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



class MaintenancePartResponse(BaseModel):
    id: int
    name: str
    part_number: Optional[str] = None
    quantity: int
    unit_cost: float
    total_cost: float

    model_config = {"from_attributes": True}

class MaintenanceLabourResponse(BaseModel):
    id: int
    description: str
    hours: float
    hourly_rate: float
    total_cost: float

    model_config = {"from_attributes": True}

class MaintenanceDocumentResponse(BaseModel):
    id: int
    document_id: uuid.UUID

    model_config = {"from_attributes": True}

class MaintenanceRecordResponse(BaseModel):
    id: int
    business_id: str
    status: MaintenanceStatus
    category: MaintenanceCategory
    
    company_id: int
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    trip_id: Optional[int] = None
    expense_id: Optional[int] = None
    
    description: Optional[str] = None
    odometer: Optional[float] = None
    cost: Optional[float] = None
    other_cost: Optional[float] = None
    other_cost: float = 0.0
    other_cost: float = 0.0
    
    workshop: Optional[str] = None
    service_provider: Optional[str] = None

    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None

    tasks: List[MaintenanceTaskResponse] = []
    parts: List[MaintenancePartResponse] = []
    labour: List[MaintenanceLabourResponse] = []
    documents: List[MaintenanceDocumentResponse] = []

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


class MaintenanceCreateRequest(BaseModel):
    vehicle_id: Optional[int] = None
    driver_id: Optional[int] = None
    trip_id: Optional[int] = None
    category: MaintenanceCategory = MaintenanceCategory.PREVENTIVE
    status: MaintenanceStatus = MaintenanceStatus.SCHEDULED
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    workshop: Optional[str] = None
    description: Optional[str] = None
    odometer: Optional[float] = None
    cost: Optional[float] = None
    other_cost: Optional[float] = None
    other_cost: float = 0.0

class MaintenanceUpdateRequest(BaseModel):
    driver_id: Optional[int] = None
    trip_id: Optional[int] = None
    status: Optional[MaintenanceStatus] = None
    completed_date: Optional[datetime] = None
    cost: Optional[float] = None
    other_cost: Optional[float] = None
    other_cost: float = 0.0
    odometer: Optional[float] = None
    description: Optional[str] = None
    workshop: Optional[str] = None

class MaintenancePartCreate(BaseModel):
    name: str
    part_number: Optional[str] = None
    quantity: int = 1
    unit_cost: float = 0.0

class MaintenancePartUpdate(BaseModel):
    name: Optional[str] = None
    part_number: Optional[str] = None
    quantity: Optional[int] = None
    unit_cost: Optional[float] = None

class MaintenanceLabourCreate(BaseModel):
    description: str
    hours: float = 1.0
    hourly_rate: float = 0.0

class MaintenanceLabourUpdate(BaseModel):
    description: Optional[str] = None
    hours: Optional[float] = None
    hourly_rate: Optional[float] = None

class MaintenanceDocumentCreate(BaseModel):
    document_id: uuid.UUID
