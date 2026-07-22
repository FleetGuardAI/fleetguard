"""
Message Gateway Framework - Validators
"""

from typing import Dict, Any, List

def validate_required_fields(payload: Dict[str, Any], required_fields: List[str]) -> bool:
    """
    Validates that all required fields are present in the payload.
    """
    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    return True

def validate_timestamp_format(timestamp_str: str) -> bool:
    """
    Validates that a string is a valid ISO format, or simply not empty if that's the channel spec.
    """
    if not timestamp_str or not isinstance(timestamp_str, str):
        raise ValueError("Timestamp must be a non-empty string.")
    return True

def validate_sender_format(sender: str) -> bool:
    """
    Validates basic sender string format.
    """
    if not sender or not isinstance(sender, str):
        raise ValueError("Sender must be a non-empty string.")
    return True
