"""
FleetGuard — Location & Routing Schemas
"""

from typing import List, Optional
from pydantic import BaseModel


class PlacePrediction(BaseModel):
    place_id: str
    description: str
    main_text: str
    secondary_text: str


class PlaceDetails(BaseModel):
    place_id: str
    formatted_address: str
    lat: float
    lng: float


class RouteAlternative(BaseModel):
    distance_km: float
    duration_hours: float
    toll_estimate: Optional[float] = None
    polyline: str
    description: Optional[str] = None


class RouteCalculationRequest(BaseModel):
    origin_lat: float
    origin_lng: float
    destination_lat: float
    destination_lng: float


class RouteCalculationResponse(BaseModel):
    distance_km: float
    duration_hours: float
    polyline: str
    toll_estimate: Optional[float] = None
    alternatives: List[RouteAlternative] = []
    source: str
