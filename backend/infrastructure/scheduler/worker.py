"""
Scheduler Service - Worker
"""

import logging
from typing import Optional
from infrastructure.scheduler.queue import BaseJobQueue
from infrastructure.scheduler.executor import JobExecutor
from infrastructure.scheduler.models import JobStatus

logger = logging.getLogger(__name__)

class JobWorker:
    """
    Consumes jobs from the queue and delegates to the executor.
    """
    def __init__(self, queue: BaseJobQueue, executor: JobExecutor):
        self.queue = queue
        self.executor = executor

    def process_next(self) -> bool:
        """
        Pulls a job from the queue and executes it.
        Returns True if a job was processed, False if queue was empty.
        """
        job = self.queue.dequeue()
        if not job:
            return False
            
        logger.info(f"Worker processing job {job.job_id}")
        self.executor.execute(job)
        return True
