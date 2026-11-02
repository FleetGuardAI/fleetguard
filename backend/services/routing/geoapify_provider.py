"""
FleetGuard — Geoapify Routing Provider
Supports commercial vehicle truck routing when configured with API key.
"""

import logging
import httpx
import polyline
from typing import List, Dict, Any, Optional
from config import settings
from services.routing.base import BaseRoutingProvider
from services.routing.schemas import RouteCalculationInput

logger = logging.getLogger("fleetguard.routing.geoapify")


class GeoapifyRoutesProvider(BaseRoutingProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEOAPIFY_API_KEY
        self.client = httpx.AsyncClient(timeout=12.0)

    @property
    def name(self) -> str:
        return "geoapify"

    @property
    def supports_truck_restrictions(self) -> bool:
        return True

    @property
    def supports_tolls(self) -> bool:
        return False

    async def compute_routes(self, req: RouteCalculationInput) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise ValueError("Geoapify API key is not configured in backend environment.")

        url = "https://api.geoapify.com/v1/routing"
        params = {
            "waypoints": f"{req.origin_lat},{req.origin_lng}|{req.destination_lat},{req.destination_lng}",
            "mode": "truck",
            "apiKey": self.api_key
        }

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException:
            raise TimeoutError("Geoapify routing request timed out.")
        except Exception as e:
            logger.error(f"Geoapify API error: {e}")
            raise

        features = data.get("features", [])
        if not features:
            return []

        results = []
        for i, feat in enumerate(features):
            props = feat.get("properties", {})
            distance_meters = props.get("distance", 0)
            duration_seconds = int(props.get("time", 0))

            coords = feat.get("geometry", {}).get("coordinates", [])
            flat_coords = []
            for pt in coords:
                if isinstance(pt[0], list):
                    for sub_pt in pt:
                        flat_coords.append((sub_pt[1], sub_pt[0]))
                else:
                    flat_coords.append((pt[1], pt[0]))

            encoded = polyline.encode(flat_coords) if flat_coords else ""

            results.append({
                "distance_km": round(distance_meters / 1000.0, 2),
                "duration_hours": round(duration_seconds / 3600.0, 2),
                "duration_seconds": duration_seconds,
                "polyline": encoded,
                "toll_estimate": None,
                "tolls_available": False,
                "summary": f"Geoapify Truck Route {i + 1}",
                "traffic_aware": False,
                "vehicle_restrictions_supported": True,
                "suitability_warning": None,
                "provider": self.name,
            })

        return results
