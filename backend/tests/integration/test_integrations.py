import os
import pytest
from unittest.mock import patch, MagicMock

from config import settings
from infrastructure.llm.openai_provider import OpenAIProvider
from services.otp_service import _send_sms
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


@pytest.mark.asyncio
@patch("twilio.rest.Client")
async def test_twilio_otp_integration(mock_twilio_client):
    """Verify Twilio SMS logic initializes and calls create message."""
    original_twilio = getattr(settings, 'TWILIO_API_KEY', None)
    settings.TWILIO_API_KEY = "dummy_twilio_key"
    
    # Mock message
    mock_msg = MagicMock()
    mock_msg.sid = "SM12345"
    mock_client_instance = mock_twilio_client.return_value
    mock_client_instance.messages.create.return_value = mock_msg

    await _send_sms("+1234567890", "123456")
    
    # Verify the mock was called correctly
    mock_twilio_client.assert_called_with("dummy_twilio_key", "dummy_twilio_key")
    mock_client_instance.messages.create.assert_called_once_with(
        body="Your FleetGuard OTP is: 123456",
        from_="+1234567890",
        to="+1234567890"
    )
    
    settings.TWILIO_API_KEY = original_twilio


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
