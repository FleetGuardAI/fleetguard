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

    def list_providers(self) -> Dict[str, Type[BaseGPSProvider]]:
        return dict(self._providers)

    def clear(self) -> None:
        """
        Clears all registered providers.
        """
        self._providers.clear()


def create_default_registry() -> GPSProviderRegistry:
    """Creates and returns a GPSProviderRegistry populated with all standard providers."""
    from infrastructure.gps.providers.generic import GenericGPSProvider
    from infrastructure.gps.providers.teltonika import TeltonikaProvider
    from infrastructure.gps.providers.queclink import QueclinkProvider
    from infrastructure.gps.providers.ruptela import RuptelaProvider
    from infrastructure.gps.providers.traccar import TraccarProvider
    from infrastructure.gps.providers.ais140 import AIS140Provider
    from infrastructure.gps.providers.gt06 import GT06Provider
    from infrastructure.gps.providers.tk103 import TK103Provider
    from infrastructure.gps.providers.mqtt import MQTTProvider

    reg = GPSProviderRegistry()
    reg.register(GenericGPSProvider)
    reg.register(TeltonikaProvider)
    reg.register(QueclinkProvider)
    reg.register(RuptelaProvider)
    reg.register(TraccarProvider)
    reg.register(AIS140Provider)
    reg.register(GT06Provider)
    reg.register(TK103Provider)
    reg.register(MQTTProvider)
    return reg
