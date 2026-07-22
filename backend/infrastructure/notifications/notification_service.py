"""
Notification Service - Core Service
"""

import logging
import uuid
import time
from typing import List, Optional
from infrastructure.notifications.models import Notification, DeliveryResult, DeliveryStatus
from infrastructure.notifications.dispatcher import NotificationDispatcher
from infrastructure.notifications.tracking import DeliveryTracker
from infrastructure.notifications.retry import RetryPolicy
from infrastructure.notifications.validators import validate_recipient, validate_message_length

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Orchestrates the dispatch, tracking, and retrying of notifications.
    """
    def __init__(self, 
                 dispatcher: NotificationDispatcher,
                 tracker: DeliveryTracker,
                 retry_policy: RetryPolicy):
        self.dispatcher = dispatcher
        self.tracker = tracker
        self.retry_policy = retry_policy

    def send(self, notification: Notification) -> List[DeliveryResult]:
        """
        Dispatches a notification to all requested channels.
        Returns a list of DeliveryResults (one per channel).
        """
        results = []
        for channel in notification.channels:
            # 1. Validation
            try:
                validate_recipient(notification.recipient, channel)
                validate_message_length(notification.message, channel)
            except ValueError as e:
                # Permanent failure on validation
                result = DeliveryResult(
                    notification_id=notification.notification_id,
                    channel=channel,
                    status=DeliveryStatus.FAILED,
                    error_message=str(e)
                )
                self.tracker.record_attempt(result)
                results.append(result)
                continue

            # 2. Dispatch
            # Check idempotency key internally (for mock purposes, we assume uniqueness is handled)
            # A real implementation would query the tracker by idempotency_key to prevent duplicate sends.

            try:
                result = self.dispatcher.dispatch(channel, notification)
                self.tracker.record_attempt(result)
                results.append(result)
            except Exception as e:
                # Transient dispatch failure
                result = DeliveryResult(
                    notification_id=notification.notification_id,
                    channel=channel,
                    status=DeliveryStatus.FAILED,
                    error_message=str(e)
                )
                self.tracker.record_attempt(result)
                results.append(result)
                
        return results

    def send_batch(self, notifications: List[Notification]) -> List[List[DeliveryResult]]:
        """
        Sends a batch of notifications.
        """
        return [self.send(n) for n in notifications]

    def retry(self, notification: Notification, channel: str) -> Optional[DeliveryResult]:
        """
        Attempts to retry a failed notification for a specific channel.
        """
        # Get history to determine retry count
        history = self.tracker.get_history(notification.notification_id)
        channel_history = [h for h in history if h.channel.value == channel]
        
        if not channel_history:
            return None
            
        latest = channel_history[-1]
        
        if latest.status == DeliveryStatus.DELIVERED:
            return latest # Already delivered
            
        current_retries = len(channel_history)
        
        # Check if we should retry
        if not self.retry_policy.should_retry(current_retries, is_permanent_failure=False): # Simplified permanent failure check
            logger.warning(f"Max retries exceeded for notification {notification.notification_id} on {channel}")
            return latest

        # Simulate delay
        delay = self.retry_policy.get_next_delay_seconds(current_retries)
        logger.debug(f"Retrying notification {notification.notification_id} in {delay} seconds...")
        # time.sleep(delay)  # In a real async worker, this would be scheduled.

        # Attempt dispatch again
        try:
            # We would parse the channel back to Enum
            enum_channel = next(c for c in notification.channels if c.value == channel)
            result = self.dispatcher.dispatch(enum_channel, notification)
            
            # Update retry count on new result
            new_result = result.model_copy(update={"retry_count": current_retries})
            self.tracker.record_attempt(new_result)
            return new_result
        except Exception as e:
            failed_result = DeliveryResult(
                notification_id=notification.notification_id,
                channel=enum_channel,
                status=DeliveryStatus.FAILED,
                error_message=str(e),
                retry_count=current_retries
            )
            self.tracker.record_attempt(failed_result)
            return failed_result

    def get_status(self, notification_id: uuid.UUID) -> Optional[DeliveryResult]:
        """
        Returns the latest tracking status.
        """
        return self.tracker.get_latest_status(notification_id)
