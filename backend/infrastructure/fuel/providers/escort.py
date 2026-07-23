"""
Fuel Sensor Gateway Framework - Escort Provider
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


class EscortProvider(BaseFuelProvider):
    @classmethod
    def key(cls) -> str:
        return "escort"

    def validate(self, payload: Dict[str, Any]) -> None:
        validate_telemetry_payload(payload, ["id", "datetime", "level"])

    def normalize(self, payload: Dict[str, Any]) -> FuelTelemetry:
        return FuelTelemetry(
            provider=self.key(),
            device_id=str(payload["id"]),
            timestamp=normalize_timestamp(payload["datetime"]),
            fuel_level=normalize_fuel_level(payload["level"]),
            measurement_unit=MeasurementUnit.ADC,
            quality=TelemetryQuality.UNKNOWN,
            temperature=normalize_temperature(payload["t"]) if "t" in payload else None,
            metadata={"raw": payload}
        )
