"""
GPS Gateway Framework — Traccar Ingestion Provider
Normalizes incoming webhook/forwarder payloads from Traccar GPS server.
Traccar forwards positions either as a JSON structure with "position" and "device"
or as a flattened position object.
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


class TraccarProvider(BaseGPSProvider):
    @classmethod
    def key(cls) -> str:
        return "traccar"

    @classmethod
    def capabilities(cls) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_ignition=True,
            supports_heading=True,
            supports_altitude=True,
            supports_speed=True
        )

    def validate(self, payload: Dict[str, Any]) -> None:
        """
        Traccar payload may contain:
        1) Nested: {"position": {...}, "device": {"uniqueId": ...}}
        2) Flat: {"uniqueId": ..., "latitude": ..., "longitude": ..., "fixTime": ...}
        """
        pos = payload.get("position", payload)
        dev = payload.get("device", {})
        
        device_id = dev.get("uniqueId") or payload.get("uniqueId") or payload.get("device_id") or pos.get("deviceId")
        if not device_id:
            raise ValueError("Traccar payload missing uniqueId or device_id")

        lat = pos.get("latitude")
        lon = pos.get("longitude")
        if lat is None or lon is None:
            raise ValueError("Traccar payload missing latitude or longitude")

    def normalize(self, payload: Dict[str, Any]) -> GPSPosition:
        pos = payload.get("position", payload)
        dev = payload.get("device", {})
        
        # Determine IMEI / device identifier
        device_id = str(dev.get("uniqueId") or payload.get("uniqueId") or payload.get("device_id") or pos.get("deviceId"))
        
        # Position fields
        lat = normalize_coordinate(pos["latitude"])
        lon = normalize_coordinate(pos["longitude"])
        
        # Timestamp: Traccar uses fixTime or deviceTime or serverTime
        ts_val = pos.get("fixTime") or pos.get("deviceTime") or pos.get("serverTime") or pos.get("timestamp")
        timestamp = normalize_timestamp(ts_val)
        
        # Speed: Traccar speed is usually in knots
        speed = None
        if "speed" in pos and pos["speed"] is not None:
            speed = normalize_speed(pos["speed"], from_unit="knots")

        heading = None
        course = pos.get("course") or pos.get("heading")
        if course is not None:
            heading = normalize_heading(course)

        altitude = None
        if "altitude" in pos and pos["altitude"] is not None:
            altitude = float(pos["altitude"])

        # Attributes: Traccar places ignition, battery, etc. in attributes dict
        attrs = pos.get("attributes", {})
        if not isinstance(attrs, dict):
            attrs = {}
            
        ignition = None
        if "ignition" in attrs:
            ignition = normalize_ignition(attrs["ignition"])
        elif "ignition" in pos:
            ignition = normalize_ignition(pos["ignition"])

        accuracy = None
        if "accuracy" in pos and pos["accuracy"] is not None:
            accuracy = float(pos["accuracy"])

        battery = None
        if "batteryLevel" in attrs:
            battery = float(attrs["batteryLevel"])
        elif "battery" in attrs:
            battery = float(attrs["battery"])

        metadata = {
            "traccar_device_name": dev.get("name"),
            "traccar_protocol": pos.get("protocol"),
            "battery": battery,
            "attributes": attrs,
            "raw": payload
        }

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
            accuracy=accuracy,
            metadata=metadata
        )
