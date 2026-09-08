"""
FleetGuard — Routing Provider Service
Abstracts interaction with Directions/Routes APIs (e.g. Google Routes API).
"""

import httpx
from typing import Optional, List
from config import settings
from schemas.location import RouteCalculationRequest, RouteCalculationResponse, RouteAlternative
import logging

logger = logging.getLogger(__name__)

class RoutingProvider:
    def __init__(self):
        self.provider = settings.ROUTING_PROVIDER
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.client = httpx.AsyncClient(timeout=15.0)
        self.default_toll_rate = settings.DEFAULT_TOLL_RATE_PER_KM

    async def calculate_route(self, request: RouteCalculationRequest) -> RouteCalculationResponse:
        # Distance calculation via haversine or mock if no API
        if self.provider != "google" or not self.api_key:
            return self._mock_route(request)
            
        try:
            # Using Google Routes API (New)
            url = "https://routes.googleapis.com/directions/v2:computeRoutes"
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                # Request distance, duration, polyline, and tolls
                "X-Goog-FieldMask": "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline,routes.travelAdvisory.tollInfo"
            }
            
            payload = {
                "origin": {
                    "location": {
                        "latLng": {
                            "latitude": request.origin_lat,
                            "longitude": request.origin_lng
                        }
                    }
                },
                "destination": {
                    "location": {
                        "latLng": {
                            "latitude": request.destination_lat,
                            "longitude": request.destination_lng
                        }
                    }
                },
                "travelMode": "DRIVE",
                "routingPreference": "TRAFFIC_AWARE",
                "computeAlternativeRoutes": True,
                "extraComputations": ["TOLLS"]
            }

            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            routes = data.get("routes", [])
            if not routes:
                return self._mock_route(request) # Fallback
                
            main_route = routes[0]
            distance_meters = main_route.get("distanceMeters", 0)
            duration_str = main_route.get("duration", "0s")
            duration_seconds = int(duration_str.rstrip('s')) if duration_str.endswith('s') else 0
            encoded_polyline = main_route.get("polyline", {}).get("encodedPolyline", "")
            
            # Tolls 
            toll_estimate = None
            toll_info = main_route.get("travelAdvisory", {}).get("tollInfo")
            if toll_info and "estimatedPrice" in toll_info:
                # E.g., [{"currencyCode": "INR", "units": "150"}]
                prices = toll_info.get("estimatedPrice", [])
                if prices:
                    # Just taking the first currency available
                    units = prices[0].get("units", "0")
                    toll_estimate = float(units)
            else:
                # Fallback to configured rate per km if toll info requested but not present
                toll_estimate = (distance_meters / 1000.0) * self.default_toll_rate
                
            # Alternatives
            alternatives = []
            if len(routes) > 1:
                for alt in routes[1:]:
                    alt_dist = alt.get("distanceMeters", 0)
                    alt_dur_str = alt.get("duration", "0s")
                    alt_dur_seconds = int(alt_dur_str.rstrip('s')) if alt_dur_str.endswith('s') else 0
                    alt_polyline = alt.get("polyline", {}).get("encodedPolyline", "")
                    
                    alt_toll = None
                    alt_toll_info = alt.get("travelAdvisory", {}).get("tollInfo")
                    if alt_toll_info and "estimatedPrice" in alt_toll_info:
                        alt_prices = alt_toll_info.get("estimatedPrice", [])
                        if alt_prices:
                            alt_toll = float(alt_prices[0].get("units", "0"))
                    
                    alternatives.append(RouteAlternative(
                        distance_km=alt_dist / 1000.0,
                        duration_hours=alt_dur_seconds / 3600.0,
                        polyline=alt_polyline,
                        toll_estimate=alt_toll
                    ))

            return RouteCalculationResponse(
                distance_km=distance_meters / 1000.0,
                duration_hours=duration_seconds / 3600.0,
                polyline=encoded_polyline,
                toll_estimate=toll_estimate,
                alternatives=alternatives,
                source="google"
            )

        except Exception as e:
            logger.error(f"Error computing route via Google: {e}")
            return self._mock_route(request)

    def _mock_route(self, request: RouteCalculationRequest) -> RouteCalculationResponse:
        import math
        # Simple Haversine distance for mock
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # radius of earth in km
            dLat = math.radians(lat2 - lat1)
            dLon = math.radians(lon2 - lon1)
            a = math.sin(dLat/2) * math.sin(dLat/2) + \
                math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
                math.sin(dLon/2) * math.sin(dLon/2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
            
        dist_km = haversine(request.origin_lat, request.origin_lng, request.destination_lat, request.destination_lng)
        
        # A straight line doesn't account for roads, multiply by 1.3 for driving factor
        driving_dist = max(1.0, dist_km * 1.3)
        # Assume 50 km/h avg speed for truck
        duration_hours = driving_dist / 50.0
        tolls = driving_dist * self.default_toll_rate
        
        # We don't have a real polyline, but returning an empty string or a simple 2-point line might break leaflet
        # so we'll encode a simple 2-point polyline manually for the mock.
        
        # Actually just returning a mock string, the frontend needs to handle it.
        # But for robustness, I'll encode a 2-point polyline.
        def encode_coords(coords):
            result = []
            prev_lat = 0
            prev_lng = 0
            for lat, lng in coords:
                lat_e5 = int(round(lat * 1e5))
                lng_e5 = int(round(lng * 1e5))
                d_lat = lat_e5 - prev_lat
                d_lng = lng_e5 - prev_lng
                prev_lat = lat_e5
                prev_lng = lng_e5
                
                for v in [d_lat, d_lng]:
                    v = ~(v << 1) if v < 0 else (v << 1)
                    while v >= 0x20:
                        result.append(chr((0x20 | (v & 0x1f)) + 63))
                        v >>= 5
                    result.append(chr(v + 63))
            return "".join(result)
            
        polyline = encode_coords([(request.origin_lat, request.origin_lng), (request.destination_lat, request.destination_lng)])
        
        return RouteCalculationResponse(
            distance_km=driving_dist,
            duration_hours=duration_hours,
            polyline=polyline,
            toll_estimate=tolls,
            alternatives=[],
            source="manual"
        )
