"""
GPS Gateway Framework - Validators
"""

from typing import Dict, Any, List

def validate_telemetry_payload(payload: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validates a raw vendor telemetry payload to ensure generic data integrity.
    Raises ValueError if validation fails. No business intelligence logic here.
    """
    for field in required_fields:
        if field not in payload:
            raise ValueError(f"Missing required field: {field}")
            
    # Latitude bounds
    if "latitude" in payload:
        lat = float(payload["latitude"])
        if lat < -90.0 or lat > 90.0:
            raise ValueError(f"Latitude {lat} is out of bounds (-90 to +90)")
            
    # Longitude bounds
    if "longitude" in payload:
        lon = float(payload["longitude"])
        if lon < -180.0 or lon > 180.0:
            raise ValueError(f"Longitude {lon} is out of bounds (-180 to +180)")
            
    # Speed bounds (basic sanity)
    if "speed" in payload:
        speed = float(payload["speed"])
        if speed < 0 or speed > 1000: # Arbitrary generic bounds to catch absurd outliers
            raise ValueError(f"Speed {speed} is out of reasonable bounds")
