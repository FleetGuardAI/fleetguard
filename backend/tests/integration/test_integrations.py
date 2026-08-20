import os
import pytest
from unittest.mock import patch, MagicMock

from config import settings
from infrastructure.llm.openai_provider import OpenAIProvider
from infrastructure.llm.openai_provider import OpenAIProvider
from infrastructure.notifications.models import Notification, NotificationChannel
from infrastructure.notifications.channels.push import PushChannel


@pytest.mark.asyncio
async def test_openai_provider_loads_api_key():
    """Verify OpenAIProvider reads API keys from settings."""
    # Temporarily override settings if not set
    original_key = settings.OPENAI_API_KEY
    settings.OPENAI_API_KEY = "dummy_test_key"
    
    provider = OpenAIProvider()
    assert provider.client.api_key == "dummy_test_key", "OpenAI provider failed to load the configured API key."
    
    settings.OPENAI_API_KEY = original_key



try:
    import firebase_admin
    HAS_FIREBASE = True
except ImportError:
    HAS_FIREBASE = False

@pytest.mark.skipif(not HAS_FIREBASE, reason="firebase_admin not installed")
@patch("infrastructure.notifications.channels.push.firebase_admin")
@patch("infrastructure.notifications.channels.push.messaging")
def test_firebase_push_notification_channel(mock_messaging, mock_firebase_admin):
    """Verify Firebase Admin SDK push notifications."""
    # Ensure apps exist so it doesn't simulate
    mock_firebase_admin._apps = {"[DEFAULT]": True}
    
    mock_response = "projects/my-project/messages/12345"
    mock_messaging.send.return_value = mock_response

    channel = PushChannel()
    
    # Create mock notification
    notification = Notification(
        recipient="mock_fcm_token",
        channels=[NotificationChannel.PUSH],
        subject="Test Title",
        message="Test Body"
    )
    
    result = channel.send(notification)
    
    assert result.status.value == "DELIVERED"
    assert result.provider_reference == mock_response
    assert mock_messaging.send.called
