"""
Message Gateway Framework - Normalizers
"""

from datetime import datetime, timezone
import dateutil.parser


def normalize_phone_number(phone: str) -> str:
    """
    Normalizes a phone number. Removes spaces, dashes, parentheses.
    Ensures it starts with '+' for E.164.
    """
    if not phone:
        return ""
    
    clean = "".join(c for c in phone if c.isdigit() or c == "+")
    if clean and not clean.startswith("+"):
        clean = "+" + clean
    return clean

def normalize_timestamp(timestamp_str: str) -> datetime:
    """
    Parses a timestamp string and ensures it is UTC-aware.
    """
    try:
        dt = dateutil.parser.isoparse(timestamp_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception as e:
        raise ValueError(f"Failed to normalize timestamp '{timestamp_str}': {e}")

def normalize_text(text: str) -> str:
    """
    Strips trailing/leading whitespace and handles empty strings.
    """
    if not text:
        return ""
    return text.strip()
