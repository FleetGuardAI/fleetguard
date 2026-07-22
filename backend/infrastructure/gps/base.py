"""
GPS Gateway Framework - Base Provider
"""

import abc
from typing import Dict, Any
from infrastructure.gps.models import GPSPosition, ProviderCapabilities


class BaseGPSProvider(abc.ABC):
    """
    Abstract Base Class for GPS Provider adaptations.
    """

    @classmethod
    @abc.abstractmethod
    def key(cls) -> str:
        """Unique key representing this provider, e.g., 'teltonika'."""
        pass

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    @classmethod
    def version(cls) -> str:
        return "1.0.0"
        
    @classmethod
    @abc.abstractmethod
    def capabilities(cls) -> ProviderCapabilities:
        """Returns what features this provider supports."""
        pass

    @abc.abstractmethod
    def validate(self, payload: Dict[str, Any]) -> None:
        """
        Validates the structure of the incoming raw vendor payload.
        Raises ValueError if invalid.
        """
        pass

    @abc.abstractmethod
    def normalize(self, payload: Dict[str, Any]) -> GPSPosition:
        """
        Translates the raw vendor payload into a standardized GPSPosition.
        """
        pass

    def receive(self, payload: Dict[str, Any]) -> GPSPosition:
        """
        Convenience pipeline: Validates and normalizes the payload.
        """
        self.validate(payload)
        return self.normalize(payload)
