"""
FleetGuard — Location Provider Service
Abstracts interaction with Places APIs (e.g. Google Places API).
"""

import httpx
from typing import List, Optional
from config import settings
from schemas.location import PlacePrediction, PlaceDetails
import logging

logger = logging.getLogger(__name__)

class LocationProvider:
    def __init__(self):
        self.provider = settings.LOCATION_PROVIDER
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        # httpx client for external calls
        self.client = httpx.AsyncClient(timeout=10.0)

    async def autocomplete(self, query: str, session_token: Optional[str] = None) -> List[PlacePrediction]:
        if not query or len(query) < 2:
            return []

        if self.provider != "google" or not self.api_key:
            # Fallback mock or none
            return [
                PlacePrediction(
                    place_id=f"mock-{query}",
                    description=f"{query} (Mock)",
                    main_text=query,
                    secondary_text="Mock Location - Add API Key"
                )
            ]

        try:
            # Google Places API Autocomplete
            url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
            params = {
                "input": query,
                "key": self.api_key,
                # Optionally restrict to components="country:IN" for India
                "components": "country:in" 
            }
            if session_token:
                params["sessiontoken"] = session_token

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            predictions = []
            for item in data.get("predictions", []):
                predictions.append(PlacePrediction(
                    place_id=item["place_id"],
                    description=item["description"],
                    main_text=item["structured_formatting"]["main_text"],
                    secondary_text=item["structured_formatting"].get("secondary_text", "")
                ))
            return predictions
        except Exception as e:
            logger.error(f"Error fetching autocomplete: {e}")
            return []

    async def get_place_details(self, place_id: str, session_token: Optional[str] = None) -> Optional[PlaceDetails]:
        if not place_id:
            return None

        if self.provider != "google" or not self.api_key:
            if place_id.startswith("mock-"):
                return PlaceDetails(
                    place_id=place_id,
                    formatted_address=place_id.replace("mock-", "") + ", India",
                    lat=28.6139, # Mock lat (New Delhi)
                    lng=77.2090  # Mock lng
                )
            return None

        try:
            # Google Places API Details
            url = "https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                "place_id": place_id,
                "key": self.api_key,
                "fields": "formatted_address,geometry"
            }
            if session_token:
                params["sessiontoken"] = session_token

            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") == "OK" and "result" in data:
                result = data["result"]
                location = result.get("geometry", {}).get("location", {})
                return PlaceDetails(
                    place_id=place_id,
                    formatted_address=result.get("formatted_address", ""),
                    lat=location.get("lat", 0.0),
                    lng=location.get("lng", 0.0)
                )
            return None
        except Exception as e:
            logger.error(f"Error fetching place details: {e}")
            return None
