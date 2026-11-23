"""
FleetGuard — Location & Routing Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PlacePrediction(BaseModel):
    place_id: str
    description: str
    main_text: str
    secondary_text: str


class PlaceDetails(BaseModel):
    place_id: str
    formatted_address: str
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude between -90 and 90 degrees")
    lng: float = Field(..., ge=-180.0, le=180.0, description="Longitude between -180 and 180 degrees")


class RouteAlternative(BaseModel):
    distance_km: float
    duration_hours: float
    toll_estimate: Optional[float] = None
    polyline: str
    description: Optional[str] = None


class RouteCalculationRequest(BaseModel):
    origin_lat: float = Field(..., ge=-90.0, le=90.0, description="Origin latitude between -90 and 90 degrees")
    origin_lng: float = Field(..., ge=-180.0, le=180.0, description="Origin longitude between -180 and 180 degrees")
    destination_lat: float = Field(..., ge=-90.0, le=90.0, description="Destination latitude between -90 and 90 degrees")
    destination_lng: float = Field(..., ge=-180.0, le=180.0, description="Destination longitude between -180 and 180 degrees")


class RouteCalculationResponse(BaseModel):
    distance_km: float
    duration_hours: float
    polyline: str
    toll_estimate: Optional[float] = None
    alternatives: List[RouteAlternative] = []
    source: str
