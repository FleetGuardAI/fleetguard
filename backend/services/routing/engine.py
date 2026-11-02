"""
FleetGuard — Unified Intelligent Routing Engine
Coordinates provider failover, cost calculation, and optimization scoring.
"""

import time
import logging
from datetime import datetime, timezone
from typing import List, Optional

from config import settings
from services.routing.schemas import RouteCalculationInput, RouteCalculationOutput, RouteOption
from services.routing.base import BaseRoutingProvider
from services.routing.google_provider import GoogleRoutesProvider
from services.routing.osrm_provider import OSRMProvider
from services.routing.geoapify_provider import GeoapifyRoutesProvider
from services.routing.cost_service import CostCalculationService
from services.routing.optimizer import RouteOptimizer

logger = logging.getLogger("fleetguard.routing.engine")


class RoutingEngine:
    """
    Production-grade routing engine orchestrating:
    - Coordinate validation
    - Multi-provider failover (Google -> OSRM / Geoapify)
    - Direct operating cost estimation
    - Multi-criteria route scoring and categorization
    """

    def __init__(self, primary_provider_name: Optional[str] = None):
        self.provider_name = (primary_provider_name or settings.ROUTING_PROVIDER or "google").lower()
        self._providers: dict[str, BaseRoutingProvider] = {
            "google": GoogleRoutesProvider(),
            "osrm": OSRMProvider(),
            "geoapify": GeoapifyRoutesProvider(),
        }

    def _validate_coordinates(self, req: RouteCalculationInput) -> None:
        if not (-90.0 <= req.origin_lat <= 90.0) or not (-180.0 <= req.origin_lng <= 180.0):
            raise ValueError(f"Invalid origin coordinates: ({req.origin_lat}, {req.origin_lng})")
        if not (-90.0 <= req.destination_lat <= 90.0) or not (-180.0 <= req.destination_lng <= 180.0):
            raise ValueError(f"Invalid destination coordinates: ({req.destination_lat}, {req.destination_lng})")

        # Check distance between origin and destination
        if abs(req.origin_lat - req.destination_lat) < 1e-5 and abs(req.origin_lng - req.destination_lng) < 1e-5:
            raise ValueError("Origin and destination coordinates are too close or identical.")

    async def calculate_routes(self, req: RouteCalculationInput) -> RouteCalculationOutput:
        start_time = time.perf_counter()
        self._validate_coordinates(req)

        raw_routes = []
        used_provider = None
        errors = []

        # 1. Attempt Primary Provider
        primary = self._providers.get(self.provider_name)
        if primary:
            try:
                logger.info(f"Attempting route calculation via primary provider: {primary.name}")
                raw_routes = await primary.compute_routes(req)
                if raw_routes:
                    used_provider = primary.name
            except Exception as e:
                logger.warning(f"Primary routing provider '{primary.name}' failed: {e}. Attempting failover.")
                errors.append(f"{primary.name}: {str(e)}")

        # 2. Failover to OSRM if primary failed or returned no routes
        if not raw_routes and self.provider_name != "osrm":
            osrm = self._providers.get("osrm")
            if osrm:
                try:
                    logger.info("Attempting route calculation via OSRM fallback engine.")
                    raw_routes = await osrm.compute_routes(req)
                    if raw_routes:
                        used_provider = osrm.name
                except Exception as e:
                    logger.error(f"Fallback routing provider OSRM also failed: {e}")
                    errors.append(f"osrm: {str(e)}")

        if not raw_routes:
            error_details = "; ".join(errors) if errors else "No driving route found between coordinates."
            raise RuntimeError(f"Unable to calculate route: {error_details}")

        # 3. Enrich each route with Cost Calculation
        for r in raw_routes:
            cost = CostCalculationService.calculate_cost(
                distance_km=r["distance_km"],
                vehicle_mileage=req.vehicle_mileage,
                fuel_price=req.fuel_price,
                toll_estimate=r.get("toll_estimate"),
                tolls_available=r.get("tolls_available", True),
                vehicle_class=req.vehicle_class,
                currency="INR"
            )
            r["cost_estimate"] = cost

        # 4. Multi-Criteria Route Optimization and Categorization
        optimized_routes = RouteOptimizer.optimize_routes(raw_routes)

        recommended = optimized_routes[0]
        exec_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return RouteCalculationOutput(
            origin_lat=req.origin_lat,
            origin_lng=req.origin_lng,
            destination_lat=req.destination_lat,
            destination_lng=req.destination_lng,
            provider=used_provider or "unknown",
            recommended_route=recommended,
            routes=optimized_routes,
            calculated_at=datetime.now(timezone.utc),
            execution_time_ms=exec_ms
        )
