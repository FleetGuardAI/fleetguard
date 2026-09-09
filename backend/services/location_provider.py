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
        self.api_key = settings.GOOGLE_MAPS_API_KEY if self.provider == "google" else settings.GEOAPIFY_API_KEY
        # httpx client for external calls
        self.client = httpx.AsyncClient(timeout=10.0)

    async def autocomplete(self, query: str, session_token: Optional[str] = None) -> List[PlacePrediction]:
        if not query or len(query) < 2:
            return []

        if self.provider not in ["google", "geoapify"] or not self.api_key:
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
            if self.provider == "geoapify":
                url = f"https://api.geoapify.com/v1/geocode/autocomplete"
                params = {
                    "text": query,
                    "apiKey": self.api_key,
                    "filter": "countrycode:in"
                }
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                predictions = []
                for feature in data.get("features", []):
                    props = feature.get("properties", {})
                    place_id = props.get("place_id")
                    formatted = props.get("formatted", "")
                    city = props.get("city", "")
                    if not place_id:
                        continue
                    predictions.append(PlacePrediction(
                        place_id=place_id,
                        description=formatted,
                        main_text=formatted.split(",")[0],
                        secondary_text=city
                    ))
                return predictions

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
        except httpx.HTTPStatusError as e:
            logger.error(f"Error fetching autocomplete HTTP {e.response.status_code}: {e.response.text}")
            return []
        except Exception as e:
            logger.error(f"Error fetching autocomplete: {e}")
            return []

    async def get_place_details(self, place_id: str, session_token: Optional[str] = None) -> Optional[PlaceDetails]:
        if not place_id:
            return None

        if self.provider not in ["google", "geoapify"] or not self.api_key:
            return PlaceDetails(
                place_id=place_id,
                formatted_address=f"Mock Location {place_id}",
                lat=28.6139,
                lng=77.2090
            )

        try:
            if self.provider == "geoapify":
                url = "https://api.geoapify.com/v2/place-details"
                params = {
                    "id": place_id,
                    "apiKey": self.api_key
                }
                response = await self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                features = data.get("features", [])
                if not features:
                    return None
                    
                props = features[0].get("properties", {})
                return PlaceDetails(
                    place_id=place_id,
                    formatted_address=props.get("formatted", ""),
                    lat=props.get("lat", 0.0),
                    lng=props.get("lon", 0.0)
                )

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
        except httpx.HTTPStatusError as e:
            logger.error(f"Error fetching place details HTTP {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error fetching place details: {e}")
            return None
