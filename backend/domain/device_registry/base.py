"""
Device Registry & Mapping Framework - Base Components
"""

import abc
import uuid
from typing import Optional, List
from domain.device_registry.models import Device, DeviceMapping, EntityType


class BaseDeviceResolver(abc.ABC):
    """
    Abstract Base Class for resolving device and mapping identities.
    """

    @abc.abstractmethod
    def resolve_device(self, provider: str, serial_number: str) -> Optional[Device]:
        """
        Resolves a hardware device from its provider-specific identifiers.
        """
        pass

    @abc.abstractmethod
    def resolve_mapping(self, device_id: uuid.UUID) -> Optional[DeviceMapping]:
        """
        Returns the active mapping for a given device, if any.
        """
        pass

    @abc.abstractmethod
    def validate_assignments(self, device: Device, entity_type: EntityType, entity_id: str) -> None:
        """
        Validates whether a device can be mapped to a specific entity.
        Raises ValueError if conflicts are found.
        """
        pass
