"""
FleetGuard — Base Routing Provider Interface
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from services.routing.schemas import RouteCalculationInput


class BaseRoutingProvider(ABC):
    """
    Abstract interface for routing engines.
    Isolates external routing APIs from trip lifecycle, persistence, and notifications.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider e.g. 'google', 'osrm', 'geoapify'"""
        pass

    @property
    @abstractmethod
    def supports_truck_restrictions(self) -> bool:
        """Whether heavy vehicle height/weight/axle constraints are respected."""
        pass

    @property
    @abstractmethod
    def supports_tolls(self) -> bool:
        """Whether toll calculation is supported."""
        pass

    @abstractmethod
    async def compute_routes(self, req: RouteCalculationInput) -> List[Dict[str, Any]]:
        """
        Calculates one or more route paths between coordinates.
        Returns a list of dicts with:
        - distance_km (float)
        - duration_hours (float)
        - duration_seconds (int)
        - polyline (str, encoded polyline)
        - toll_estimate (Optional[float])
        - tolls_available (bool)
        - summary (Optional[str])
        - traffic_aware (bool)
        - vehicle_restrictions_supported (bool)
        - suitability_warning (Optional[str])
        """
        pass
