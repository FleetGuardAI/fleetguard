"""
Notification Service - Push Channel (Firebase FCM)
"""
import logging
import uuid
import os
from datetime import datetime, timezone

from infrastructure.notifications.models import Notification, DeliveryResult, DeliveryStatus, NotificationChannel
from infrastructure.notifications.channels.base import BaseNotificationChannel

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except ImportError:
    firebase_admin = None

logger = logging.getLogger(__name__)

class PushChannel(BaseNotificationChannel):
    def __init__(self):
        # Initialize Firebase Admin if not already initialized and if creds exist
        cred_path = os.path.join(os.getcwd(), "firebase-adminsdk.json")
        if firebase_admin and not firebase_admin._apps:
            if os.path.exists(cred_path):
                try:
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase Admin SDK initialized successfully.")
                except Exception as e:
                    logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            else:
                logger.warning(f"Firebase credentials not found at {cred_path}")

    def send(self, notification: Notification) -> DeliveryResult:
        if not firebase_admin or not firebase_admin._apps:
            logger.warning("Firebase Admin not initialized, simulating Push dispatch.")
            return DeliveryResult(
                notification_id=notification.notification_id,
                channel=NotificationChannel.PUSH,
                status=DeliveryStatus.SENT,
                provider_reference=f"push-sim-{uuid.uuid4().hex[:8]}",
                delivered_at=datetime.now(timezone.utc)
            )

        try:
            # Recipient is assumed to be an FCM device token
            message = messaging.Message(
                notification=messaging.Notification(
                    title=notification.subject or "FleetGuard Notification",
                    body=notification.message,
                ),
                token=notification.recipient,
            )
            response = messaging.send(message)
            return DeliveryResult(
                notification_id=notification.notification_id,
                channel=NotificationChannel.PUSH,
                status=DeliveryStatus.DELIVERED,
                provider_reference=response,
                delivered_at=datetime.now(timezone.utc)
            )
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return DeliveryResult(
                notification_id=notification.notification_id,
                channel=NotificationChannel.PUSH,
                status=DeliveryStatus.FAILED,
                error_message=str(e)
            )
