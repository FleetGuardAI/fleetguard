"""
FleetGuard — Google Routes API Provider
Computes routes, traffic-aware durations, polylines, and toll estimates using Google Maps Routes API.
"""

import logging
import httpx
from typing import List, Dict, Any, Optional
from config import settings
from services.routing.base import BaseRoutingProvider
from services.routing.schemas import RouteCalculationInput

logger = logging.getLogger("fleetguard.routing.google")


class GoogleRoutesProvider(BaseRoutingProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GOOGLE_MAPS_API_KEY
        self.client = httpx.AsyncClient(timeout=12.0)

    @property
    def name(self) -> str:
        return "google"

    @property
    def supports_truck_restrictions(self) -> bool:
        # Standard Routes API uses DRIVE mode unless specialized truck routing add-on is provisioned
        return False

    @property
    def supports_tolls(self) -> bool:
        return True

    async def compute_routes(self, req: RouteCalculationInput) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise ValueError("Google Maps API key is not configured in backend environment.")

        url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline,"
                "routes.travelAdvisory.tollInfo,routes.description"
            ),
        }

        payload = {
            "origin": {
                "location": {
                    "latLng": {"latitude": req.origin_lat, "longitude": req.origin_lng}
                }
            },
            "destination": {
                "location": {
                    "latLng": {"latitude": req.destination_lat, "longitude": req.destination_lng}
                }
            },
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE",
            "computeAlternativeRoutes": True,
            "routeModifiers": {
                "avoidTolls": req.avoid_tolls,
                "avoidHighways": req.avoid_highways,
            },
            "extraComputations": ["TOLLS"],
        }

        try:
            response = await self.client.post(url, headers=headers, json=payload)
            if response.status_code == 403:
                raise PermissionError("Google Maps Routes API rejected the key (insufficient permissions or invalid key).")
            if response.status_code == 429:
                raise RuntimeError("Google Maps Routes API rate limit exceeded.")
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException:
            logger.warning("Google Routes API timed out after 12 seconds.")
            raise TimeoutError("Google Routes API request timed out.")
        except httpx.HTTPStatusError as e:
            logger.error(f"Google Routes API HTTP error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"Google Routes API error: {e.response.status_code}")

        raw_routes = data.get("routes", [])
        if not raw_routes:
            return []

        results = []
        for i, r in enumerate(raw_routes):
            dist_meters = r.get("distanceMeters", 0)
            dist_km = round(dist_meters / 1000.0, 2)

            dur_str = r.get("duration", "0s")
            dur_seconds = int(dur_str.rstrip("s")) if dur_str.endswith("s") else 0
            dur_hours = round(dur_seconds / 3600.0, 2)

            poly = r.get("polyline", {}).get("encodedPolyline", "")

            # Parse Tolls
            toll_estimate = None
            tolls_available = False
            toll_info = r.get("travelAdvisory", {}).get("tollInfo")
            if toll_info and "estimatedPrice" in toll_info:
                prices = toll_info.get("estimatedPrice", [])
                if prices:
                    units = prices[0].get("units", "0")
                    toll_estimate = float(units)
                    tolls_available = True

            results.append({
                "distance_km": dist_km,
                "duration_hours": dur_hours,
                "duration_seconds": dur_seconds,
                "polyline": poly,
                "toll_estimate": toll_estimate,
                "tolls_available": tolls_available,
                "summary": r.get("description", f"Google Route {i + 1}"),
                "traffic_aware": True,
                "vehicle_restrictions_supported": False,
                "suitability_warning": (
                    "Passenger vehicle road network used; physical commercial vehicle restrictions (height/axle) not fully validated by Google Routes."
                    if req.vehicle_class and req.vehicle_class.upper() in ["HEAVY_DUTY", "TRAILER", "TANKER"]
                    else None
                ),
                "provider": self.name,
            })

        return results
