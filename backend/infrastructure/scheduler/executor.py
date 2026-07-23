"""
Scheduler Service - Executor
"""

import time
import logging
from datetime import datetime, timezone
from typing import Optional
from infrastructure.scheduler.models import Job, JobExecution, JobStatus
from infrastructure.scheduler.registry import JobRegistry
from infrastructure.scheduler.tracking import JobTracker

logger = logging.getLogger(__name__)

class JobExecutor:
    """
    Executes a single job by resolving its handler from the registry.
    """
    def __init__(self, registry: JobRegistry, tracker: JobTracker):
        self.registry = registry
        self.tracker = tracker

    def execute(self, job: Job, retry_number: int = 0) -> JobExecution:
        """
        Executes the job and records the result.
        """
        start_time = datetime.now(timezone.utc)
        start_ts = time.time()
        
        execution = JobExecution(
            job_id=job.job_id,
            started_at=start_time,
            status=JobStatus.RUNNING,
            retry_number=retry_number
        )
        self.tracker.record_execution(execution)
        
        try:
            handler = self.registry.resolve(job.job_type)
            handler(job.payload)
            
            end_ts = time.time()
            completed_execution = execution.model_copy(update={
                "status": JobStatus.COMPLETED,
                "completed_at": datetime.now(timezone.utc),
                "duration_ms": int((end_ts - start_ts) * 1000)
            })
            self.tracker.record_execution(completed_execution)
            return completed_execution
            
        except Exception as e:
            end_ts = time.time()
            failed_execution = execution.model_copy(update={
                "status": JobStatus.FAILED,
                "completed_at": datetime.now(timezone.utc),
                "duration_ms": int((end_ts - start_ts) * 1000),
                "error": str(e)
            })
            self.tracker.record_execution(failed_execution)
            return failed_execution
