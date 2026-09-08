"""
FleetGuard — Location & Routing API Router
Provides APIs for location autocomplete, place details, and route calculation.
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from services.auth_service import get_current_user
from models.user import User
from services.location_provider import LocationProvider
from services.routing_provider import RoutingProvider
from schemas.location import PlacePrediction, PlaceDetails, RouteCalculationRequest, RouteCalculationResponse

router = APIRouter(prefix="/v1", tags=["Location & Routing"])

@router.get("/locations/autocomplete", response_model=List[PlacePrediction])
async def autocomplete_location(
    query: str = Query(..., min_length=2),
    session_token: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
) -> List[PlacePrediction]:
    """Get location autocomplete predictions based on a query string."""
    provider = LocationProvider()
    return await provider.autocomplete(query, session_token)

@router.get("/locations/details", response_model=PlaceDetails)
async def get_place_details(
    place_id: str = Query(...),
    session_token: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
) -> PlaceDetails:
    """Get precise coordinates and formatted address for a place ID."""
    provider = LocationProvider()
    details = await provider.get_place_details(place_id, session_token)
    if not details:
        raise HTTPException(status_code=404, detail="Place not found or details unavailable")
    return details

@router.post("/routes/calculate", response_model=RouteCalculationResponse)
async def calculate_route(
    request: RouteCalculationRequest,
    current_user: User = Depends(get_current_user)
) -> RouteCalculationResponse:
    """Calculate driving route distance, duration, polyline, and tolls."""
    provider = RoutingProvider()
    return await provider.calculate_route(request)
