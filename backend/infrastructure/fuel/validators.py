"""
Fuel Sensor Gateway Framework - Validators
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
            
    # Check that fuel level is a number (if present in payload)
    if "fuel_level" in payload:
        try:
            float(payload["fuel_level"])
        except (ValueError, TypeError):
            raise ValueError(f"Fuel level must be a number, got: {payload['fuel_level']}")
