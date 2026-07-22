"""
Fuel Sensor Gateway Framework - Normalizers
"""

from datetime import datetime, timezone
from typing import Any
from infrastructure.fuel.models import MeasurementUnit, TelemetryQuality

def normalize_fuel_level(value: Any) -> float:
    """
    Normalizes fuel level to a float with reasonable precision.
    """
    return round(float(value), 4)

def normalize_temperature(value: Any) -> float:
    """
    Normalizes temperature to Celsius with reasonable precision.
    """
    return round(float(value), 2)

def normalize_measurement_unit(value: Any) -> MeasurementUnit:
    """
    Normalizes various vendor string units to standard MeasurementUnit.
    """
    if isinstance(value, str):
        val_upper = value.upper()
        if val_upper in ["L", "LITERS", "LITRES"]:
            return MeasurementUnit.LITRES
        if val_upper in ["%", "PERCENT", "PERCENTAGE"]:
            return MeasurementUnit.PERCENTAGE
        if val_upper in ["MM", "MILLIMETERS", "MILLIMETRES"]:
            return MeasurementUnit.MILLIMETERS
        if val_upper in ["V", "VOLTS", "VOLTAGE"]:
            return MeasurementUnit.VOLTAGE
        if val_upper in ["ADC", "RAW"]:
            return MeasurementUnit.ADC
    elif isinstance(value, MeasurementUnit):
        return value
        
    return MeasurementUnit.UNKNOWN

def normalize_quality(value: Any) -> TelemetryQuality:
    """
    Normalizes telemetry quality indicators.
    """
    if isinstance(value, str):
        val_upper = value.upper()
        if val_upper in ["HIGH", "GOOD", "RELIABLE"]:
            return TelemetryQuality.HIGH
        if val_upper in ["MEDIUM", "OK", "AVERAGE"]:
            return TelemetryQuality.MEDIUM
        if val_upper in ["LOW", "POOR", "UNRELIABLE"]:
            return TelemetryQuality.LOW
    elif isinstance(value, TelemetryQuality):
        return value
        
    return TelemetryQuality.UNKNOWN

def normalize_timestamp(value: Any) -> datetime:
    """
    Normalizes timestamp to UTC ISO-8601.
    """
    if isinstance(value, (int, float)):
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
