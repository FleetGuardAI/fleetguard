"""
Scheduler Service - Repositories
"""

import abc
import uuid
from typing import List, Optional, Dict
from infrastructure.scheduler.models import Job, JobExecution, JobStatus
from infrastructure.scheduler.errors import JobNotFound

class BaseJobRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, job: Job) -> None:
        pass
        
    @abc.abstractmethod
    def get(self, job_id: uuid.UUID) -> Optional[Job]:
        pass
        
    @abc.abstractmethod
    def list_all(self) -> List[Job]:
        pass

    @abc.abstractmethod
    def delete(self, job_id: uuid.UUID) -> None:
        pass


class BaseExecutionRepository(abc.ABC):
    @abc.abstractmethod
    def save(self, execution: JobExecution) -> None:
        pass
        
    @abc.abstractmethod
    def get(self, execution_id: uuid.UUID) -> Optional[JobExecution]:
        pass
        
    @abc.abstractmethod
    def get_by_job(self, job_id: uuid.UUID) -> List[JobExecution]:
        pass


class InMemoryJobRepository(BaseJobRepository):
    def __init__(self):
        self._jobs: Dict[uuid.UUID, Job] = {}

    def save(self, job: Job) -> None:
        self._jobs[job.job_id] = job
        
    def get(self, job_id: uuid.UUID) -> Optional[Job]:
        return self._jobs.get(job_id)
        
    def list_all(self) -> List[Job]:
        return list(self._jobs.values())

    def delete(self, job_id: uuid.UUID) -> None:
        if job_id in self._jobs:
            del self._jobs[job_id]


class InMemoryExecutionRepository(BaseExecutionRepository):
    def __init__(self):
        self._executions: List[JobExecution] = []

    def save(self, execution: JobExecution) -> None:
        self._executions.append(execution)
        
    def get(self, execution_id: uuid.UUID) -> Optional[JobExecution]:
        # Return the latest state for this execution_id
        matches = [ex for ex in self._executions if ex.execution_id == execution_id]
        return matches[-1] if matches else None
        
    def get_by_job(self, job_id: uuid.UUID) -> List[JobExecution]:
        return [ex for ex in self._executions if ex.job_id == job_id]
