"""
GPS Gateway Framework — AIS-140 Provider
Supports Indian AIS-140 standard telematics packets and JSON representations.
AIS-140 fields: IMEI, packet_type, timestamp, latitude, longitude, speed, heading, altitude, ignition, panic_switch, battery.
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


class AIS140Provider(BaseGPSProvider):
    @classmethod
    def key(cls) -> str:
        return "ais140"

    @classmethod
    def capabilities(cls) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_ignition=True,
            supports_heading=True,
            supports_altitude=True,
            supports_speed=True
        )

    def validate(self, payload: Dict[str, Any]) -> None:
        imei = payload.get("imei") or payload.get("device_id")
        if not imei:
            raise ValueError("AIS-140 payload missing IMEI or device_id")
        if "latitude" not in payload or "longitude" not in payload:
            raise ValueError("AIS-140 payload missing latitude or longitude")

    def normalize(self, payload: Dict[str, Any]) -> GPSPosition:
        imei = str(payload.get("imei") or payload.get("device_id"))
        lat = normalize_coordinate(payload["latitude"])
        lon = normalize_coordinate(payload["longitude"])
        
        ts_val = payload.get("timestamp") or payload.get("datetime") or payload.get("gps_time")
        timestamp = normalize_timestamp(ts_val)
        
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

        emergency = payload.get("emergency_status") or payload.get("panic_button", False)

        return GPSPosition(
            provider=self.key(),
            device_id=imei,
            latitude=lat,
            longitude=lon,
            altitude=altitude,
            heading=heading,
            speed=speed,
            ignition=ignition,
            timestamp=timestamp,
            accuracy=float(payload.get("accuracy", 1.0)) if "accuracy" in payload else None,
            metadata={
                "emergency_status": emergency,
                "battery_voltage": payload.get("battery_voltage"),
                "raw": payload
            }
        )
