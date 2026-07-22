"""
Notification Service - Channel Base
"""

import abc
from infrastructure.notifications.models import Notification, DeliveryResult

class BaseNotificationChannel(abc.ABC):
    """
    Abstract interface for notification channel integrations.
    """
    
    @abc.abstractmethod
    def send(self, notification: Notification) -> DeliveryResult:
        """
        Attempts to deliver the notification via the underlying provider API.
        Returns a DeliveryResult indicating success or failure.
        """
        pass
