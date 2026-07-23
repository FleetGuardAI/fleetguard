"""
GPS Gateway Framework - Ruptela Provider
"""

from typing import Dict, Any
from infrastructure.gps.base import BaseGPSProvider
from infrastructure.gps.models import GPSPosition, ProviderCapabilities
from infrastructure.gps.validators import validate_telemetry_payload
from infrastructure.gps.normalizers import (
    normalize_coordinate, 
    normalize_timestamp, 
    normalize_speed, 
    normalize_heading,
    normalize_ignition
)


class RuptelaProvider(BaseGPSProvider):
    @classmethod
    def key(cls) -> str:
        return "ruptela"

    @classmethod
    def capabilities(cls) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_ignition=True,
            supports_heading=True,
            supports_altitude=True,
            supports_speed=True
        )

    def validate(self, payload: Dict[str, Any]) -> None:
        validate_telemetry_payload(payload, ["device_id", "lat", "lon", "ts"])

    def normalize(self, payload: Dict[str, Any]) -> GPSPosition:
        # Ruptela stub format
        
        return GPSPosition(
            provider=self.key(),
            device_id=str(payload["device_id"]),
            latitude=normalize_coordinate(payload["lat"]),
            longitude=normalize_coordinate(payload["lon"]),
            altitude=float(payload["alt"]) if "alt" in payload else None,
            heading=normalize_heading(payload["heading"]) if "heading" in payload else None,
            speed=normalize_speed(payload["spd"], from_unit="km/h") if "spd" in payload else None,
            ignition=normalize_ignition(payload["ign"]) if "ign" in payload else None,
            timestamp=normalize_timestamp(payload["ts"]),
            metadata={"raw": payload}
        )
