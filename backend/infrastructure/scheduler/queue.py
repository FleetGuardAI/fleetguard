"""
Scheduler Service - Queue
"""

import abc
from typing import List, Optional
from infrastructure.scheduler.models import Job

class BaseJobQueue(abc.ABC):
    @abc.abstractmethod
    def enqueue(self, job: Job) -> None:
        """Pushes a job onto the execution queue."""
        pass
        
    @abc.abstractmethod
    def dequeue(self) -> Optional[Job]:
        """Pops a job from the queue for execution."""
        pass

    @abc.abstractmethod
    def get_size(self) -> int:
        pass


class InMemoryJobQueue(BaseJobQueue):
    def __init__(self):
        self._queue: List[Job] = []

    def enqueue(self, job: Job) -> None:
        self._queue.append(job)
        
    def dequeue(self) -> Optional[Job]:
        if not self._queue:
            return None
        return self._queue.pop(0)

    def get_size(self) -> int:
        return len(self._queue)
