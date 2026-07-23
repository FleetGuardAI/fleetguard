"""
Fuel Sensor Gateway Framework - Generic Provider
"""

from typing import Dict, Any
from infrastructure.fuel.base import BaseFuelProvider
from infrastructure.fuel.models import FuelTelemetry, MeasurementUnit, TelemetryQuality
from infrastructure.fuel.validators import validate_telemetry_payload
from infrastructure.fuel.normalizers import (
    normalize_fuel_level,
    normalize_temperature,
    normalize_measurement_unit,
    normalize_quality,
    normalize_timestamp
)


class GenericFuelProvider(BaseFuelProvider):
    @classmethod
    def key(cls) -> str:
        return "generic"

    def validate(self, payload: Dict[str, Any]) -> None:
        validate_telemetry_payload(payload, ["device_id", "timestamp", "fuel_level"])

    def normalize(self, payload: Dict[str, Any]) -> FuelTelemetry:
        unit = MeasurementUnit.UNKNOWN
        if "unit" in payload:
            unit = normalize_measurement_unit(payload["unit"])
            
        quality = TelemetryQuality.UNKNOWN
        if "quality" in payload:
            quality = normalize_quality(payload["quality"])
            
        temp = None
        if "temperature" in payload:
            temp = normalize_temperature(payload["temperature"])

        return FuelTelemetry(
            provider=self.key(),
            device_id=str(payload["device_id"]),
            timestamp=normalize_timestamp(payload["timestamp"]),
            fuel_level=normalize_fuel_level(payload["fuel_level"]),
            measurement_unit=unit,
            quality=quality,
            temperature=temp,
            sensor_health=str(payload["status"]) if "status" in payload else None,
            metadata={"raw": payload}
        )
