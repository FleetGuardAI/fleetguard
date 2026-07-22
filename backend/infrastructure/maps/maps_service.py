"""
Maps Service - Core Service
"""

import math
import logging
from typing import List, Optional
from infrastructure.maps.config import MapsConfig
from infrastructure.maps.models import Coordinate, Address, Route, Geofence
from infrastructure.maps.validators import validate_coordinate, validate_radius, validate_address_string
from infrastructure.maps.errors import MapsServiceUnavailable, RouteCalculationFailed

logger = logging.getLogger(__name__)


class MapsService:
    """
    Lightweight infrastructure service for geospatial operations.
    Configured statically via MapsConfig.
    """
    def __init__(self, config: MapsConfig = None):
        self.config = config or MapsConfig()

    def reverse_geocode(self, coordinate: Coordinate) -> Address:
        """
        Converts a coordinate into a human-readable address.
        """
        # Validate input bounds
        validate_coordinate(coordinate.latitude, coordinate.longitude)
        
        # In a real implementation, this would make an HTTP request to Google Maps Geocoding API.
        # We simulate the API call boundary here for tests to mock.
        return self._make_reverse_geocode_request(coordinate)
        
    def forward_geocode(self, address_string: str) -> Coordinate:
        """
        Converts an address string into a coordinate.
        """
        validate_address_string(address_string)
        return self._make_forward_geocode_request(address_string)

    def calculate_route(self, origin: Coordinate, destination: Coordinate) -> Route:
        """
        Calculates a route between two coordinates.
        """
        validate_coordinate(origin.latitude, origin.longitude)
        validate_coordinate(destination.latitude, destination.longitude)
        return self._make_route_request(origin, destination)

    def calculate_eta(self, origin: Coordinate, destination: Coordinate) -> int:
        """
        Returns the ETA in seconds between two points.
        """
        route = self.calculate_route(origin, destination)
        return route.duration_seconds

    def calculate_distance(self, point1: Coordinate, point2: Coordinate) -> float:
        """
        Calculates straight-line (Haversine) distance between two points in meters.
        This does not require an API call.
        """
        validate_coordinate(point1.latitude, point1.longitude)
        validate_coordinate(point2.latitude, point2.longitude)
        
        R = 6371e3  # Earth radius in meters
        phi1 = math.radians(point1.latitude)
        phi2 = math.radians(point2.latitude)
        delta_phi = math.radians(point2.latitude - point1.latitude)
        delta_lambda = math.radians(point2.longitude - point1.longitude)
        
        a = math.sin(delta_phi / 2) * math.sin(delta_phi / 2) + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2) * math.sin(delta_lambda / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return round(distance, 2)

    def snap_to_road(self, path: List[Coordinate]) -> List[Coordinate]:
        """
        Snaps a series of GPS coordinates to the nearest road.
        """
        for coord in path:
            validate_coordinate(coord.latitude, coord.longitude)
        return self._make_snap_to_road_request(path)

    def is_inside_geofence(self, coordinate: Coordinate, geofence: Geofence) -> bool:
        """
        Evaluates if a coordinate is strictly inside a circular geofence.
        Does not require an API call.
        """
        validate_coordinate(coordinate.latitude, coordinate.longitude)
        validate_radius(geofence.radius_meters)
        
        distance = self.calculate_distance(coordinate, geofence.center)
        return distance <= geofence.radius_meters

    # --- Internal mockable request boundaries ---
    
    def _make_reverse_geocode_request(self, coordinate: Coordinate) -> Address:
        raise NotImplementedError("API integration mocked in tests.")
        
    def _make_forward_geocode_request(self, address_string: str) -> Coordinate:
        raise NotImplementedError("API integration mocked in tests.")
        
    def _make_route_request(self, origin: Coordinate, destination: Coordinate) -> Route:
        raise NotImplementedError("API integration mocked in tests.")
        
    def _make_snap_to_road_request(self, path: List[Coordinate]) -> List[Coordinate]:
        raise NotImplementedError("API integration mocked in tests.")
