"""
Scheduler Service - Validators
"""

from datetime import datetime, timezone
from infrastructure.scheduler.models import JobPriority, ScheduleType

def validate_schedule_time(scheduled_at: datetime, schedule_type: ScheduleType) -> None:
    """
    Validates that scheduled time is not strictly in the past for delayed jobs.
    """
    if schedule_type == ScheduleType.DELAYED:
        now = datetime.now(timezone.utc)
        if scheduled_at < now:
            raise ValueError("Delayed jobs cannot be scheduled in the past.")

def validate_payload(payload: dict) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a dictionary.")
