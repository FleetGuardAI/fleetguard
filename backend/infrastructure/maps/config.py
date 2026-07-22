"""
Maps Service - Configuration
"""

from pydantic_settings import BaseSettings
from typing import Dict, Any

class MapsConfig(BaseSettings):
    """
    Configuration for the Maps Service.
    Configured statically for Google Maps (currently).
    """
    MAPS_API_KEY: str = "DUMMY_KEY"
    MAPS_BASE_URL: str = "https://maps.googleapis.com/maps/api"
    MAPS_REQUEST_TIMEOUT_SECONDS: int = 10
    MAPS_MAX_RETRIES: int = 3
    
    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }
