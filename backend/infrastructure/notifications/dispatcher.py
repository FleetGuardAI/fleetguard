"""
Notification Service - Dispatcher
"""

from typing import Dict, Type
from infrastructure.notifications.models import NotificationChannel, Notification, DeliveryResult
from infrastructure.notifications.channels.base import BaseNotificationChannel
from infrastructure.notifications.channels.email import EmailChannel
from infrastructure.notifications.channels.sms import SMSChannel
from infrastructure.notifications.channels.webhook import WebhookChannel
from infrastructure.notifications.channels.push import PushChannel

class NotificationDispatcher:
    """
    Routes notifications to the appropriate requested channel implementation.
    """
    def __init__(self):
        # Statically configured provider implementations
        self._channels: Dict[NotificationChannel, BaseNotificationChannel] = {
            NotificationChannel.EMAIL: EmailChannel(),
            NotificationChannel.SMS: SMSChannel(),
            NotificationChannel.WEBHOOK: WebhookChannel(),
            NotificationChannel.PUSH: PushChannel()
        }

    def dispatch(self, channel_enum: NotificationChannel, notification: Notification) -> DeliveryResult:
        """
        Dispatches the notification to the specific channel provider.
        """
        provider = self._channels.get(channel_enum)
        if not provider:
            raise NotImplementedError(f"No channel provider registered for {channel_enum.value}")
            
        return provider.send(notification)
