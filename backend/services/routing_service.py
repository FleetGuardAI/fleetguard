"""
FleetGuard — Routing Service

Abstract routing interface. Currently uses planned_distance from user input.
Can be extended with Google Maps / Mapbox later without changing Trip Intelligence.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class RouteEstimate:
    distance_km: Optional[float]
    duration_hours: Optional[float]
    toll_estimate: Optional[float]
    source: str
    confidence: str


class RoutingService:
    """
    Service to provide routing estimates.
    """
    
    async def estimate_route(
        self, 
        origin: str, 
        destination: str, 
        planned_distance: Optional[float]
    ) -> RouteEstimate:
        """
        Estimate the route distance and time.
        Currently relies entirely on user input (planned_distance).
        Does NOT invent fake routing intelligence.
        """
        confidence = "MEDIUM" if planned_distance and planned_distance > 0 else "INSUFFICIENT"
        
        return RouteEstimate(
            distance_km=planned_distance,
            duration_hours=None,  # Unknown without a real maps API
            toll_estimate=None,   # Unknown without a real maps API
            source="user_input",
            confidence=confidence
        )
