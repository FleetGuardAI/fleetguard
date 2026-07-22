"""
Scheduler Service - Models
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"


class ScheduleType(str, Enum):
    ONCE = "ONCE"
    DELAYED = "DELAYED"
    RECURRING = "RECURRING"


class JobPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RetryPolicy(BaseModel):
    max_attempts: int = 3
    initial_delay: int = 5
    exponential_backoff: bool = True
    max_delay: int = 3600

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class RecurrencePolicy(BaseModel):
    interval_seconds: int
    max_executions: Optional[int] = None

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class Job(BaseModel):
    """
    Immutable representation of a job definition.
    """
    job_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    job_name: str
    job_type: str
    schedule_type: ScheduleType = ScheduleType.ONCE
    priority: JobPriority = JobPriority.NORMAL
    scheduled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict)
    retry_policy: RetryPolicy = Field(default_factory=RetryPolicy)
    recurrence_policy: Optional[RecurrencePolicy] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class JobExecution(BaseModel):
    """
    Immutable representation of a job execution instance.
    """
    execution_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    job_id: uuid.UUID
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    status: JobStatus = JobStatus.RUNNING
    duration_ms: int = 0
    error: Optional[str] = None
    retry_number: int = 0

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
