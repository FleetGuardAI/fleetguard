"""
Notification Service - Retry Policy
"""

class RetryPolicy:
    """
    Configurable retry strategy for failed notifications.
    """
    def __init__(self, max_retries: int = 3, base_delay_seconds: int = 5):
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds

    def should_retry(self, current_retry_count: int, is_permanent_failure: bool = False) -> bool:
        """
        Determines if a notification should be retried.
        Permanent failures (e.g., 400 Bad Request invalid recipient) bypass retries.
        """
        if is_permanent_failure:
            return False
        return current_retry_count < self.max_retries

    def get_next_delay_seconds(self, current_retry_count: int) -> int:
        """
        Calculates exponential backoff delay.
        """
        if current_retry_count < 0:
            return 0
        return self.base_delay_seconds * (2 ** current_retry_count)
