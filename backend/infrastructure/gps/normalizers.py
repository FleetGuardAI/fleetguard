"""
GPS Gateway Framework - Normalizers
"""

from datetime import datetime, timezone
from typing import Any, Optional

def normalize_coordinate(value: Any) -> float:
    """
    Normalizes a coordinate to a float with reasonable precision.
    """
    return round(float(value), 6)

def normalize_speed(value: Any, from_unit: str = "km/h") -> float:
    """
    Normalizes speed to km/h.
    """
    speed = float(value)
    if from_unit.lower() == "mph":
        return round(speed * 1.60934, 2)
    elif from_unit.lower() in ["m/s", "ms"]:
        return round(speed * 3.6, 2)
    elif from_unit.lower() == "knots":
        return round(speed * 1.852, 2)
    return round(speed, 2)

def normalize_heading(value: Any) -> float:
    """
    Normalizes heading to 0-360 degrees.
    """
    heading = float(value)
    heading = heading % 360
    if heading < 0:
        heading += 360
    return round(heading, 2)

def normalize_ignition(value: Any) -> bool:
    """
    Normalizes various ignition states to boolean.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0
    if isinstance(value, str):
        val_lower = value.lower()
        if val_lower in ["true", "1", "on", "yes", "active"]:
            return True
        if val_lower in ["false", "0", "off", "no", "inactive"]:
            return False
    return False

def normalize_timestamp(value: Any) -> datetime:
    """
    Normalizes timestamp to UTC ISO-8601.
    If it's an integer, assumes unix timestamp (seconds).
    If it's a string, parses it.
    """
    if isinstance(value, int) or isinstance(value, float):
        # Determine if it's ms or s based on length
        if value > 1e11: # likely milliseconds
            return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc)
        return datetime.fromtimestamp(value, tz=timezone.utc)
        
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            pass
            
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
        
    raise ValueError(f"Cannot normalize timestamp from value: {value}")
