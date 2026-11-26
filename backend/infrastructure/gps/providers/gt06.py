"""
GPS Gateway Framework — GT06 / GT06N Provider
Supports Concox / Jimi GT06 protocol packets and JSON representations.
"""

from typing import Dict, Any
from infrastructure.gps.base import BaseGPSProvider
from infrastructure.gps.models import GPSPosition, ProviderCapabilities
from infrastructure.gps.normalizers import (
    normalize_coordinate,
    normalize_timestamp,
    normalize_speed,
    normalize_heading,
    normalize_ignition
)


class GT06Provider(BaseGPSProvider):
    @classmethod
    def key(cls) -> str:
        return "gt06"

    @classmethod
    def capabilities(cls) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_ignition=True,
            supports_heading=True,
            supports_altitude=False,
            supports_speed=True
        )

    def validate(self, payload: Dict[str, Any]) -> None:
        imei = payload.get("imei") or payload.get("device_id")
        if not imei:
            raise ValueError("GT06 payload missing imei / device_id")
        if "latitude" not in payload or "longitude" not in payload:
            raise ValueError("GT06 payload missing latitude or longitude")

    def normalize(self, payload: Dict[str, Any]) -> GPSPosition:
        device_id = str(payload.get("imei") or payload.get("device_id"))
        lat = normalize_coordinate(payload["latitude"])
        lon = normalize_coordinate(payload["longitude"])
        timestamp = normalize_timestamp(payload.get("timestamp") or payload.get("datetime"))

        speed = None
        if "speed" in payload and payload["speed"] is not None:
            speed = normalize_speed(payload["speed"], from_unit="km/h")

        heading = None
        if "heading" in payload and payload["heading"] is not None:
            heading = normalize_heading(payload["heading"])

        ignition = None
        if "ignition" in payload and payload["ignition"] is not None:
            ignition = normalize_ignition(payload["ignition"])

        return GPSPosition(
            provider=self.key(),
            device_id=device_id,
            latitude=lat,
            longitude=lon,
            altitude=None,
            heading=heading,
            speed=speed,
            ignition=ignition,
            timestamp=timestamp,
            accuracy=float(payload.get("accuracy", 1.0)) if "accuracy" in payload else None,
            metadata={"protocol": "GT06", "raw": payload}
        )
