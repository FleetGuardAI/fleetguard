"""
GPS Gateway Framework - Teltonika Provider
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


class TeltonikaProvider(BaseGPSProvider):
    @classmethod
    def key(cls) -> str:
        return "teltonika"

    @classmethod
    def capabilities(cls) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_ignition=True,
            supports_heading=True,
            supports_altitude=True,
            supports_speed=True
        )

    def validate(self, payload: Dict[str, Any]) -> None:
        validate_telemetry_payload(payload, ["imei", "latitude", "longitude", "timestamp"])

    def normalize(self, payload: Dict[str, Any]) -> GPSPosition:
        # Teltonika uses 'imei' instead of generic 'device_id'
        
        return GPSPosition(
            provider=self.key(),
            device_id=str(payload["imei"]),
            latitude=normalize_coordinate(payload["latitude"]),
            longitude=normalize_coordinate(payload["longitude"]),
            altitude=float(payload["altitude"]) if "altitude" in payload else None,
            heading=normalize_heading(payload["heading"]) if "heading" in payload else None,
            speed=normalize_speed(payload["speed"], from_unit="km/h") if "speed" in payload else None,
            ignition=normalize_ignition(payload["ignition"]) if "ignition" in payload else None,
            timestamp=normalize_timestamp(payload["timestamp"]),
            metadata={"raw": payload}
        )
