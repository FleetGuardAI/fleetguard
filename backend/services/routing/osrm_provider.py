"""
FleetGuard — Open Source Routing Machine (OSRM) Provider
Calculates genuine road driving routes, distances, durations, and polylines via OSRM.
"""

import logging
import httpx
from typing import List, Dict, Any
from services.routing.base import BaseRoutingProvider
from services.routing.schemas import RouteCalculationInput

logger = logging.getLogger("fleetguard.routing.osrm")


class OSRMProvider(BaseRoutingProvider):
    """
    Open Source Routing Machine (OSRM) provider based on OpenStreetMap road networks.
    Computes real road-network navigation without requiring proprietary API tokens.
    """

    def __init__(self, base_url: str = "https://router.project-osrm.org"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=10.0)

    @property
    def name(self) -> str:
        return "osrm"

    @property
    def supports_truck_restrictions(self) -> bool:
        # Standard OSRM car profile uses OpenStreetMap car driving rules
        return False

    @property
    def supports_tolls(self) -> bool:
        return False

    async def compute_routes(self, req: RouteCalculationInput) -> List[Dict[str, Any]]:
        # OSRM coordinate order: {longitude},{latitude};{longitude},{latitude}
        coords = f"{req.origin_lng},{req.origin_lat};{req.destination_lng},{req.destination_lat}"
        url = f"{self.base_url}/route/v1/driving/{coords}"
        params = {
            "overview": "full",
            "geometries": "polyline",  # Google encoded polyline format
            "alternatives": "true",
            "steps": "false",
        }

        try:
            response = await self.client.get(url, params=params)
            if response.status_code == 429:
                raise RuntimeError("OSRM rate limit encountered.")
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException:
            logger.warning("OSRM request timed out after 10s.")
            raise TimeoutError("OSRM routing service timed out.")
        except httpx.HTTPStatusError as e:
            logger.error(f"OSRM HTTP error: {e.response.status_code}")
            raise RuntimeError(f"OSRM error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"OSRM connection error: {e}")
            raise

        if data.get("code") != "Ok":
            logger.warning(f"OSRM returned status code: {data.get('code')}")
            return []

        raw_routes = data.get("routes", [])
        results = []
        for i, r in enumerate(raw_routes):
            dist_meters = r.get("distance", 0.0)
            dist_km = round(dist_meters / 1000.0, 2)

            dur_seconds = int(r.get("duration", 0))
            dur_hours = round(dur_seconds / 3600.0, 2)

            poly = r.get("geometry", "")

            results.append({
                "distance_km": dist_km,
                "duration_hours": dur_hours,
                "duration_seconds": dur_seconds,
                "polyline": poly,
                "toll_estimate": None,
                "tolls_available": False,
                "summary": f"OSM Road Route {i + 1}",
                "traffic_aware": False,
                "vehicle_restrictions_supported": False,
                "suitability_warning": (
                    "OpenStreetMap general road profile used; physical commercial vehicle restrictions (height/weight/axle) not enforced."
                    if req.vehicle_class and req.vehicle_class.upper() in ["HEAVY_DUTY", "TRAILER", "TANKER"]
                    else None
                ),
                "provider": self.name,
            })

        return results
