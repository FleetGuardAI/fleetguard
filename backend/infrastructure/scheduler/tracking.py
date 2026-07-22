"""
Scheduler Service - Tracking
"""

from typing import List
import uuid
from infrastructure.scheduler.models import JobExecution
from infrastructure.scheduler.repository import BaseExecutionRepository

class JobTracker:
    """
    Maintains an append-only execution history via the repository.
    """
    def __init__(self, repository: BaseExecutionRepository):
        self.repository = repository

    def record_execution(self, execution: JobExecution) -> None:
        """
        Records an execution state. Never overwrites.
        Since executions have unique execution_ids, saving a new model appends.
        """
        self.repository.save(execution)

    def get_history(self, job_id: uuid.UUID) -> List[JobExecution]:
        """
        Returns all execution attempts for a job.
        """
        return self.repository.get_by_job(job_id)
