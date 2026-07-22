"""
GPS Gateway Framework - Unknown Provider
"""

from typing import Dict, Any
from infrastructure.gps.base import BaseGPSProvider
from infrastructure.gps.models import GPSPosition, ProviderCapabilities
from datetime import datetime, timezone


class UnknownProvider(BaseGPSProvider):
    @classmethod
    def key(cls) -> str:
        return "unknown"

    @classmethod
    def capabilities(cls) -> ProviderCapabilities:
        return ProviderCapabilities()

    def validate(self, payload: Dict[str, Any]) -> None:
        raise ValueError("Cannot validate payload for unknown provider.")

    def normalize(self, payload: Dict[str, Any]) -> GPSPosition:
        raise ValueError("Cannot normalize payload for unknown provider.")
