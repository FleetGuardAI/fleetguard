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
            # Google Places API (New) Autocomplete
            url = "https://places.googleapis.com/v1/places:autocomplete"
            headers = {
                "X-Goog-Api-Key": self.api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "input": query,
                "includedRegionCodes": ["IN"]
            }
            if session_token:
                payload["sessionToken"] = session_token

            response = await self.client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            predictions = []
            for item in data.get("suggestions", []):
                pred = item.get("placePrediction")
                if not pred:
                    continue
                struct = pred.get("structuredFormat", {})
                predictions.append(PlacePrediction(
                    place_id=pred.get("placeId", ""),
                    description=pred.get("text", {}).get("text", ""),
                    main_text=struct.get("mainText", {}).get("text", ""),
                    secondary_text=struct.get("secondaryText", {}).get("text", "")
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
            # Google Places API (New) Details
            url = f"https://places.googleapis.com/v1/places/{place_id}"
            headers = {
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": "id,formattedAddress,location"
            }
            params = {}
            if session_token:
                params["sessionToken"] = session_token

            response = await self.client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            location = data.get("location", {})
            return PlaceDetails(
                place_id=data.get("id", place_id),
                formatted_address=data.get("formattedAddress", ""),
                lat=location.get("latitude", 0.0),
                lng=location.get("longitude", 0.0)
            )
            return None
        except Exception as e:
            logger.error(f"Error fetching place details: {e}")
            return None
