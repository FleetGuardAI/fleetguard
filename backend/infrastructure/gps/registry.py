"""
GPS Gateway Framework - Registry
"""

from typing import Dict, Type
import logging
from infrastructure.gps.base import BaseGPSProvider


logger = logging.getLogger(__name__)


class GPSProviderRegistry:
    """
    Registry for GPS Providers.
    """
    def __init__(self):
        self._providers: Dict[str, Type[BaseGPSProvider]] = {}

    def register(self, provider_class: Type[BaseGPSProvider]) -> None:
        """
        Registers a provider.
        Raises ValueError if a provider with the same key is already registered.
        """
        key = provider_class.key()
        
        if key in self._providers:
            raise ValueError(f"GPS Provider with key '{key}' is already registered.")
            
        self._providers[key] = provider_class
        logger.debug(f"Registered GPS Provider: {key}")

    def get_provider(self, key: str) -> BaseGPSProvider:
        """
        Retrieves a provider by key.
        Raises KeyError if not found.
        """
        if key not in self._providers:
            raise KeyError(f"No GPS Provider registered with key '{key}'")
            
        provider_class = self._providers[key]
        return provider_class()

    def clear(self) -> None:
        """
        Clears all registered providers.
        """
        self._providers.clear()
