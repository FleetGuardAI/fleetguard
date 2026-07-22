"""
Scheduler Service - Retry
"""

from infrastructure.scheduler.models import RetryPolicy

class RetryHelper:
    @staticmethod
    def should_retry(retry_policy: RetryPolicy, current_attempt: int) -> bool:
        return current_attempt < retry_policy.max_attempts

    @staticmethod
    def calculate_delay_seconds(retry_policy: RetryPolicy, current_attempt: int) -> int:
        if not retry_policy.exponential_backoff:
            return retry_policy.initial_delay
            
        delay = retry_policy.initial_delay * (2 ** current_attempt)
        return min(delay, retry_policy.max_delay)
