"""
Fuel Sensor Gateway Framework - Base Provider
"""

import abc
from typing import Dict, Any
from infrastructure.fuel.models import FuelTelemetry


class BaseFuelProvider(abc.ABC):
    """
    Abstract Base Class for Fuel Sensor Provider adaptations.
    """

    @classmethod
    @abc.abstractmethod
    def key(cls) -> str:
        """Unique key representing this provider, e.g., 'omnicomm'."""
        pass

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    @classmethod
    def version(cls) -> str:
        return "1.0.0"

    @abc.abstractmethod
    def validate(self, payload: Dict[str, Any]) -> None:
        """
        Validates the structure of the incoming raw vendor payload.
        Raises ValueError if invalid.
        """
        pass

    @abc.abstractmethod
    def normalize(self, payload: Dict[str, Any]) -> FuelTelemetry:
        """
        Translates the raw vendor payload into a standardized FuelTelemetry object.
        """
        pass

    def receive(self, payload: Dict[str, Any]) -> FuelTelemetry:
        """
        Convenience pipeline: Validates and normalizes the payload.
        """
        self.validate(payload)
        return self.normalize(payload)
