"""
Notification Service - Validators
"""

import re
from typing import List
from infrastructure.notifications.models import NotificationChannel, NotificationPriority

def validate_recipient(recipient: str, channel: NotificationChannel) -> None:
    """
    Validates recipient string formatting based on the channel.
    Raises ValueError if invalid.
    """
    if not recipient:
        raise ValueError("Recipient cannot be empty.")
        
    if channel == NotificationChannel.EMAIL:
        # Basic naive email validation
        if not re.match(r"[^@]+@[^@]+\.[^@]+", recipient):
            raise ValueError(f"Invalid email recipient: {recipient}")
            
    elif channel in (NotificationChannel.SMS, NotificationChannel.WHATSAPP):
        # Basic naive phone validation (e.g. requires + and digits)
        if not re.match(r"^\+[1-9]\d{1,14}$", recipient):
            raise ValueError(f"Invalid phone recipient: {recipient}")
            
    elif channel == NotificationChannel.WEBHOOK:
        if not recipient.startswith("http://") and not recipient.startswith("https://"):
            raise ValueError(f"Invalid webhook URL: {recipient}")


def validate_message_length(message: str, channel: NotificationChannel) -> None:
    """
    Validates that the message does not exceed channel limits.
    Raises ValueError if exceeded.
    """
    if not message:
        raise ValueError("Message cannot be empty.")
        
    limits = {
        NotificationChannel.SMS: 160,
        NotificationChannel.WHATSAPP: 4096,
        NotificationChannel.EMAIL: 100000,
        NotificationChannel.WEBHOOK: 1000000
    }
    
    limit = limits.get(channel)
    if limit and len(message) > limit:
        raise ValueError(f"Message exceeds maximum length of {limit} for channel {channel.value}.")
