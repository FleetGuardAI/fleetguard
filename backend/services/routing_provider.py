"""
FleetGuard — Routing Provider Service Adapter
Integrates the RoutingEngine with existing legacy schemas and callers.
"""

import logging
from typing import Optional, List
from config import settings
from schemas.location import RouteCalculationRequest, RouteCalculationResponse, RouteAlternative
from services.routing.engine import RoutingEngine
from services.routing.schemas import RouteCalculationInput

logger = logging.getLogger(__name__)


class RoutingProvider:
    """
    Adapter maintaining backwards compatibility with schemas.location.RouteCalculationResponse
    while delegating to the production-grade RoutingEngine with OSRM failover and real geometries.
    """

    def __init__(self):
        self.engine = RoutingEngine()

    async def calculate_route(self, request: RouteCalculationRequest) -> RouteCalculationResponse:
        input_data = RouteCalculationInput(
            origin_lat=request.origin_lat,
            origin_lng=request.origin_lng,
            destination_lat=request.destination_lat,
            destination_lng=request.destination_lng,
        )

        output = await self.engine.calculate_routes(input_data)
        recommended = output.recommended_route

        # Map alternatives
        alternatives = []
        for alt in output.routes:
            if alt.id != recommended.id:
                alternatives.append(
                    RouteAlternative(
                        distance_km=alt.distance_km,
                        duration_hours=alt.duration_hours,
                        polyline=alt.polyline,
                        toll_estimate=alt.toll_estimate,
                        description=f"{alt.category_label}: {alt.selection_reason or alt.summary}"
                    )
                )

        return RouteCalculationResponse(
            distance_km=recommended.distance_km,
            duration_hours=recommended.duration_hours,
            polyline=recommended.polyline,
            toll_estimate=recommended.toll_estimate,
            alternatives=alternatives,
            source=output.provider
        )
