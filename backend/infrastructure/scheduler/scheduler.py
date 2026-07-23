"""
Scheduler Service - Scheduler
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional
import uuid
from infrastructure.scheduler.models import Job, JobStatus, ScheduleType
from infrastructure.scheduler.repository import BaseJobRepository
from infrastructure.scheduler.queue import BaseJobQueue
from infrastructure.scheduler.validators import validate_schedule_time, validate_payload

logger = logging.getLogger(__name__)

class Scheduler:
    """
    Orchestrates job persistence and determines when jobs are eligible for queueing.
    """
    def __init__(self, repository: BaseJobRepository, queue: BaseJobQueue):
        self.repository = repository
        self.queue = queue

    def schedule(self, job: Job) -> Job:
        """
        Persists a job and queues it if immediately due.
        """
        validate_schedule_time(job.scheduled_at, job.schedule_type)
        validate_payload(job.payload)
        
        self.repository.save(job)
        
        if job.schedule_type == ScheduleType.ONCE or job.scheduled_at <= datetime.now(timezone.utc):
            self.queue.enqueue(job)
            
        return job
        
    def cancel(self, job_id: uuid.UUID) -> None:
        """
        Removes a job from the repository, preventing future executions.
        """
        self.repository.delete(job_id)

    def get_job(self, job_id: uuid.UUID) -> Optional[Job]:
        """
        Retrieves a scheduled job.
        """
        return self.repository.get(job_id)

    def enqueue_due_jobs(self) -> int:
        """
        Scans the repository for jobs that are due for execution and pushes them to the queue.
        In a real system, this would be a polled process.
        """
        now = datetime.now(timezone.utc)
        all_jobs = self.repository.list_all()
        enqueued_count = 0
        
        for job in all_jobs:
            if job.scheduled_at <= now:
                self.queue.enqueue(job)
                enqueued_count += 1
                
                # If ONCE or DELAYED, it is one-time execution so we remove it from the schedule.
                # If RECURRING, we would calculate next run time and update the job.
                if job.schedule_type in (ScheduleType.ONCE, ScheduleType.DELAYED):
                    self.repository.delete(job.job_id)
                elif job.schedule_type == ScheduleType.RECURRING and job.recurrence_policy:
                    # Very naive recurrence handling for this mock
                    # In a robust system, we would calculate the next strict interval tick
                    from datetime import timedelta
                    next_run = now + timedelta(seconds=job.recurrence_policy.interval_seconds)
                    updated_job = job.model_copy(update={"scheduled_at": next_run})
                    self.repository.save(updated_job)
                    
        return enqueued_count
