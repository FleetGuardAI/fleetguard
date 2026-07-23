"""
Maps Service - Validators
"""

from infrastructure.maps.models import Coordinate
from infrastructure.maps.errors import InvalidCoordinate, InvalidAddress

def validate_coordinate(lat: float, lon: float) -> Coordinate:
    """
    Validates lat/lon bounds and returns a Coordinate.
    """
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        raise InvalidCoordinate("Latitude and longitude must be numbers.")
        
    if not (-90.0 <= lat <= 90.0):
        raise InvalidCoordinate(f"Latitude must be between -90 and 90, got {lat}")
        
    if not (-180.0 <= lon <= 180.0):
        raise InvalidCoordinate(f"Longitude must be between -180 and 180, got {lon}")
        
    return Coordinate(latitude=float(lat), longitude=float(lon))


def validate_radius(radius: float) -> float:
    """
    Validates a geofence radius.
    """
    if not isinstance(radius, (int, float)):
        raise ValueError("Radius must be a number.")
    if radius <= 0:
        raise ValueError("Radius must be strictly positive.")
    return float(radius)


def validate_address_string(address: str) -> str:
    """
    Validates an address string is not empty.
    """
    if not isinstance(address, str) or not address.strip():
        raise InvalidAddress("Address string cannot be empty.")
    return address.strip()
