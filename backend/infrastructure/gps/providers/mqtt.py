"""
GPS Gateway Framework — MQTT Telematics Provider
Normalizes telemetry published by connected vehicles over MQTT JSON topics.
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


class MQTTProvider(BaseGPSProvider):
    @classmethod
    def key(cls) -> str:
        return "mqtt"

    @classmethod
    def capabilities(cls) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_ignition=True,
            supports_heading=True,
            supports_altitude=True,
            supports_speed=True
        )

    def validate(self, payload: Dict[str, Any]) -> None:
        device_id = payload.get("device_id") or payload.get("imei") or payload.get("client_id")
        if not device_id:
            raise ValueError("MQTT payload missing device_id or imei")
        if "latitude" not in payload or "longitude" not in payload:
            raise ValueError("MQTT payload missing latitude or longitude")

    def normalize(self, payload: Dict[str, Any]) -> GPSPosition:
        device_id = str(payload.get("device_id") or payload.get("imei") or payload.get("client_id"))
        lat = normalize_coordinate(payload["latitude"])
        lon = normalize_coordinate(payload["longitude"])
        timestamp = normalize_timestamp(payload.get("timestamp") or payload.get("time"))

        speed = None
        if "speed" in payload and payload["speed"] is not None:
            speed = normalize_speed(payload["speed"], from_unit="km/h")

        heading = None
        if "heading" in payload and payload["heading"] is not None:
            heading = normalize_heading(payload["heading"])

        altitude = None
        if "altitude" in payload and payload["altitude"] is not None:
            altitude = float(payload["altitude"])

        ignition = None
        if "ignition" in payload and payload["ignition"] is not None:
            ignition = normalize_ignition(payload["ignition"])

        return GPSPosition(
            provider=self.key(),
            device_id=device_id,
            latitude=lat,
            longitude=lon,
            altitude=altitude,
            heading=heading,
            speed=speed,
            ignition=ignition,
            timestamp=timestamp,
            accuracy=float(payload.get("accuracy", 1.0)) if "accuracy" in payload else None,
            metadata={"protocol": "MQTT", "raw": payload}
        )
