import pytest
import os
from unittest.mock import patch, MagicMock

# Set required env vars for app initialization before importing app modules
os.environ["OCR_PROVIDER"] = "mock"
os.environ["GOOGLE_DOCUMENT_AI_PROJECT_ID"] = "test"
os.environ["GOOGLE_DOCUMENT_AI_PROCESSOR_ID"] = "test"
os.environ["GOOGLE_DOCUMENT_AI_LOCATION"] = "us"

from services.routing_provider import RoutingProvider
from services.location_provider import LocationProvider
from schemas.location import RouteCalculationRequest

@pytest.mark.asyncio
async def test_location_autocomplete_mocked():
    with patch("config.settings.GOOGLE_MAPS_API_KEY", "test"), \
         patch("config.settings.LOCATION_PROVIDER", "google"):
        provider = LocationProvider()
        
        from unittest.mock import AsyncMock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "suggestions": [
                {
                    "placePrediction": {
                        "placeId": "test_id_123",
                        "text": {"text": "Mumbai"},
                        "structuredFormat": {
                            "mainText": {"text": "Mumbai"},
                            "secondaryText": {"text": "Maharashtra, India"}
                        }
                    }
                }
            ]
        }
        provider.client.post = AsyncMock(return_value=mock_response)
        
        results = await provider.autocomplete("Mumbai")
        print("DEBUG RESULTS:", results)
        print("DEBUG CALL:", provider.client.post.call_args)
        assert len(results) == 1
        assert results[0].place_id == "test_id_123"
        assert results[0].main_text == "Mumbai"

@pytest.mark.asyncio
async def test_routing_provider_fallback():
    provider = RoutingProvider()
    
    # Without Google API key configured, should use haversine fallback
    with patch("config.settings.GOOGLE_MAPS_API_KEY", ""):
        req = RouteCalculationRequest(
            origin_lat=20.0,
            origin_lng=70.0,
            destination_lat=21.0,
            destination_lng=71.0
        )
        res = await provider.calculate_route(req)
        
        assert res.source == "manual"
        assert res.distance_km is not None
        assert res.distance_km > 100 # Rough distance
        assert res.duration_hours is not None
