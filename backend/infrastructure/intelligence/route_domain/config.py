"""
Fleet Intelligence Engine - Route Intelligence Config
"""

from typing import List
from pydantic import BaseModel


class RouteIntelligenceConfig(BaseModel):
    """
    Configuration parameters for the Route Intelligence domain.
    Abstracts business thresholds to keep domain checks deterministic and pure.
    """
    maximum_route_deviation_meters: float = 500.0
    maximum_trip_delay_minutes: float = 30.0
    maximum_stop_duration_minutes: float = 15.0
    unauthorized_stop_threshold_minutes: float = 5.0
    restricted_geofence_ids: List[str] = []
    permitted_route_variance_percentage: float = 10.0

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
