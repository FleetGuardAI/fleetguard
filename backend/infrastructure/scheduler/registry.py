"""
Scheduler Service - Registry
"""

from typing import Callable, Dict
from infrastructure.scheduler.errors import HandlerNotRegistered

class JobRegistry:
    """
    Registry for resolving job handlers without coupling to business logic.
    """
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}

    def register(self, job_type: str, handler: Callable) -> None:
        """
        Registers a callable handler for a specific job_type.
        """
        self._handlers[job_type] = handler

    def unregister(self, job_type: str) -> None:
        """
        Unregisters a handler.
        """
        if job_type in self._handlers:
            del self._handlers[job_type]

    def resolve(self, job_type: str) -> Callable:
        """
        Returns the handler for a job_type, or raises HandlerNotRegistered.
        """
        handler = self._handlers.get(job_type)
        if not handler:
            raise HandlerNotRegistered(f"No handler registered for job type: {job_type}")
        return handler
