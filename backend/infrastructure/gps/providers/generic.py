"""
GPS Gateway Framework - Generic Provider
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


class GenericGPSProvider(BaseGPSProvider):
    @classmethod
    def key(cls) -> str:
        return "generic"

    @classmethod
    def capabilities(cls) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_ignition=True,
            supports_heading=True,
            supports_altitude=True,
            supports_speed=True
        )

    def validate(self, payload: Dict[str, Any]) -> None:
        validate_telemetry_payload(payload, ["device_id", "latitude", "longitude", "timestamp"])

    def normalize(self, payload: Dict[str, Any]) -> GPSPosition:
        lat = normalize_coordinate(payload["latitude"])
        lon = normalize_coordinate(payload["longitude"])
        timestamp = normalize_timestamp(payload["timestamp"])
        
        speed = None
        if "speed" in payload:
            speed = normalize_speed(payload["speed"], from_unit="km/h")
            
        heading = None
        if "heading" in payload:
            heading = normalize_heading(payload["heading"])
            
        altitude = None
        if "altitude" in payload:
            altitude = float(payload["altitude"])
            
        ignition = None
        if "ignition" in payload:
            ignition = normalize_ignition(payload["ignition"])

        return GPSPosition(
            provider=self.key(),
            device_id=str(payload["device_id"]),
            latitude=lat,
            longitude=lon,
            altitude=altitude,
            heading=heading,
            speed=speed,
            ignition=ignition,
            timestamp=timestamp,
            accuracy=float(payload.get("accuracy", 0.0)) if "accuracy" in payload else None,
            metadata={"raw": payload}
        )
