"""
Notification Service - SMS Channel Stub
"""

from infrastructure.notifications.models import Notification, DeliveryResult, DeliveryStatus, NotificationChannel
from infrastructure.notifications.channels.base import BaseNotificationChannel
from datetime import datetime, timezone
import uuid

class SMSChannel(BaseNotificationChannel):
    def send(self, notification: Notification) -> DeliveryResult:
        # Simulate SMS API Call
        return DeliveryResult(
            notification_id=notification.notification_id,
            channel=NotificationChannel.SMS,
            status=DeliveryStatus.DELIVERED,
            provider_reference=f"sms-{uuid.uuid4().hex[:8]}",
            delivered_at=datetime.now(timezone.utc)
        )
