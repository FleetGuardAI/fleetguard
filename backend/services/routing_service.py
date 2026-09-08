"""
FleetGuard — Routing Service

Abstract routing interface. Currently uses planned_distance from user input.
Can be extended with Google Maps / Mapbox later without changing Trip Intelligence.
"""

from typing import Optional
from dataclasses import dataclass
from schemas.location import RouteCalculationRequest, RouteCalculationResponse
from services.routing_provider import RoutingProvider

@dataclass
class RouteEstimate:
    distance_km: Optional[float]
    duration_hours: Optional[float]
    toll_estimate: Optional[float]
    source: str
    confidence: str
    polyline: Optional[str] = None


class RoutingService:
    """
    Service to provide routing estimates.
    """
    
    def __init__(self):
        self.provider = RoutingProvider()
        
    async def estimate_route(
        self, 
        origin: str, 
        destination: str, 
        planned_distance: Optional[float] = None,
        origin_lat: Optional[float] = None,
        origin_lng: Optional[float] = None,
        destination_lat: Optional[float] = None,
        destination_lng: Optional[float] = None,
        pre_calculated_distance: Optional[float] = None,
        pre_calculated_duration: Optional[float] = None
    ) -> RouteEstimate:
        """
        Estimate the route distance and time.
        If pre_calculated_distance is provided (from frontend calling /calculate), use it.
        If coordinates are provided, use the routing provider.
        If only text is provided, fall back to planned_distance.
        """
        if pre_calculated_distance is not None:
            return RouteEstimate(
                distance_km=pre_calculated_distance,
                duration_hours=pre_calculated_duration,
                toll_estimate=None, # Frontend passes toll in cost if needed
                source="google", # Assuming frontend used the API
                confidence="HIGH",
                polyline=None
            )
            
        if origin_lat is not None and origin_lng is not None and destination_lat is not None and destination_lng is not None:
            req = RouteCalculationRequest(
                origin_lat=origin_lat,
                origin_lng=origin_lng,
                destination_lat=destination_lat,
                destination_lng=destination_lng
            )
            resp = await self.provider.calculate_route(req)
            confidence = "HIGH" if resp.source == "google" else "MEDIUM"
            return RouteEstimate(
                distance_km=resp.distance_km,
                duration_hours=resp.duration_hours,
                toll_estimate=resp.toll_estimate,
                source=resp.source,
                confidence=confidence,
                polyline=resp.polyline
            )

        # Fallback to planned_distance if no coordinates provided
        confidence = "MEDIUM" if planned_distance and planned_distance > 0 else "INSUFFICIENT"
        
        return RouteEstimate(
            distance_km=planned_distance,
            duration_hours=None,  
            toll_estimate=None,   
            source="user_input",
            confidence=confidence,
            polyline=None
        )
