"""
Fuel Sensor Gateway Framework - Unknown Provider
"""

from typing import Dict, Any
from infrastructure.fuel.base import BaseFuelProvider
from infrastructure.fuel.models import FuelTelemetry


class UnknownProvider(BaseFuelProvider):
    @classmethod
    def key(cls) -> str:
        return "unknown"

    def validate(self, payload: Dict[str, Any]) -> None:
        raise ValueError("Cannot validate payload for unknown provider.")

    def normalize(self, payload: Dict[str, Any]) -> FuelTelemetry:
        raise ValueError("Cannot normalize payload for unknown provider.")
