"""
Notification Service - Delivery Tracking
"""

from typing import List, Dict, Optional
import uuid
from infrastructure.notifications.models import DeliveryResult

class DeliveryTracker:
    """
    Append-only tracking for notification delivery results.
    Maintains complete lifecycle of each notification for auditing.
    """
    def __init__(self):
        # In a real system, this writes to a database log table
        self._history: List[DeliveryResult] = []

    def record_attempt(self, result: DeliveryResult) -> None:
        """
        Records a delivery attempt result.
        """
        self._history.append(result)

    def get_history(self, notification_id: uuid.UUID) -> List[DeliveryResult]:
        """
        Returns the full delivery history for a notification across all channels.
        """
        return [r for r in self._history if r.notification_id == notification_id]
        
    def get_latest_status(self, notification_id: uuid.UUID) -> Optional[DeliveryResult]:
        """
        Returns the most recent delivery result for a notification.
        """
        history = self.get_history(notification_id)
        if not history:
            return None
        return history[-1]
