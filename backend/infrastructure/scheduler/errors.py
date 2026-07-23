"""
Scheduler Service - Errors
"""

class SchedulerError(Exception):
    """Base exception for all Scheduler errors."""
    pass

class InvalidSchedule(SchedulerError):
    pass

class JobNotFound(SchedulerError):
    pass

class JobExecutionFailed(SchedulerError):
    pass

class HandlerNotRegistered(SchedulerError):
    pass

class RetryLimitExceeded(SchedulerError):
    pass
