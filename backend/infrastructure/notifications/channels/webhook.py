"""
Notification Service - Webhook Channel Stub
"""

from infrastructure.notifications.models import Notification, DeliveryResult, DeliveryStatus, NotificationChannel
from infrastructure.notifications.channels.base import BaseNotificationChannel
from datetime import datetime, timezone
import uuid

class WebhookChannel(BaseNotificationChannel):
    def send(self, notification: Notification) -> DeliveryResult:
        return DeliveryResult(
            notification_id=notification.notification_id,
            channel=NotificationChannel.WEBHOOK,
            status=DeliveryStatus.DELIVERED,
            provider_reference=f"hook-{uuid.uuid4().hex[:8]}",
            delivered_at=datetime.now(timezone.utc)
        )
