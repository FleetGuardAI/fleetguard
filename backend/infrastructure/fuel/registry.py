"""
Fuel Sensor Gateway Framework - Registry
"""

from typing import Dict, Type
import logging
from infrastructure.fuel.base import BaseFuelProvider


logger = logging.getLogger(__name__)


class FuelProviderRegistry:
    """
    Registry for Fuel Sensor Providers.
    """
    def __init__(self):
        self._providers: Dict[str, Type[BaseFuelProvider]] = {}

    def register(self, provider_class: Type[BaseFuelProvider]) -> None:
        """
        Registers a provider.
        Raises ValueError if a provider with the same key is already registered.
        """
        key = provider_class.key()
        
        if key in self._providers:
            raise ValueError(f"Fuel Provider with key '{key}' is already registered.")
            
        self._providers[key] = provider_class
        logger.debug(f"Registered Fuel Provider: {key}")

    def get_provider(self, key: str) -> BaseFuelProvider:
        """
        Retrieves a provider by key.
        Raises KeyError if not found.
        """
        if key not in self._providers:
            raise KeyError(f"No Fuel Provider registered with key '{key}'")
            
        provider_class = self._providers[key]
        return provider_class()

    def clear(self) -> None:
        """
        Clears all registered providers.
        """
        self._providers.clear()
