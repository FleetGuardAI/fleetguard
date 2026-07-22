"""
Fuel Sensor Gateway Framework - Omnicomm Provider
"""

from typing import Dict, Any
from infrastructure.fuel.base import BaseFuelProvider
from infrastructure.fuel.models import FuelTelemetry, MeasurementUnit, TelemetryQuality
from infrastructure.fuel.validators import validate_telemetry_payload
from infrastructure.fuel.normalizers import (
    normalize_fuel_level,
    normalize_temperature,
    normalize_timestamp
)


class OmnicommProvider(BaseFuelProvider):
    @classmethod
    def key(cls) -> str:
        return "omnicomm"

    def validate(self, payload: Dict[str, Any]) -> None:
        validate_telemetry_payload(payload, ["sensor_id", "time", "level"])

    def normalize(self, payload: Dict[str, Any]) -> FuelTelemetry:
        # Omnicomm raw frequency mapped to something, or raw level
        
        return FuelTelemetry(
            provider=self.key(),
            device_id=str(payload["sensor_id"]),
            timestamp=normalize_timestamp(payload["time"]),
            fuel_level=normalize_fuel_level(payload["level"]),
            measurement_unit=MeasurementUnit.ADC, # Often raw ADC
            quality=TelemetryQuality.HIGH, # Hardcoded stub
            temperature=normalize_temperature(payload["temp"]) if "temp" in payload else None,
            sensor_health=None,
            metadata={"raw": payload}
        )
