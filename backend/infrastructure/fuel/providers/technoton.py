"""
Fuel Sensor Gateway Framework - Technoton Provider
"""

from typing import Dict, Any
from infrastructure.fuel.base import BaseFuelProvider
from infrastructure.fuel.models import FuelTelemetry, MeasurementUnit, TelemetryQuality
from infrastructure.fuel.validators import validate_telemetry_payload
from infrastructure.fuel.normalizers import (
    normalize_fuel_level,
    normalize_timestamp
)


class TechnotonProvider(BaseFuelProvider):
    @classmethod
    def key(cls) -> str:
        return "technoton"

    def validate(self, payload: Dict[str, Any]) -> None:
        validate_telemetry_payload(payload, ["mac", "ts", "freq"])

    def normalize(self, payload: Dict[str, Any]) -> FuelTelemetry:
        return FuelTelemetry(
            provider=self.key(),
            device_id=str(payload["mac"]),
            timestamp=normalize_timestamp(payload["ts"]),
            fuel_level=normalize_fuel_level(payload["freq"]),
            measurement_unit=MeasurementUnit.UNKNOWN, # frequency isn't in our enum, could add HZ later
            quality=TelemetryQuality.UNKNOWN,
            metadata={"raw": payload}
        )
