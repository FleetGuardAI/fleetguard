"""
Device Registry & Mapping Framework - Mapping Service
"""

import uuid
from typing import List, Optional
from datetime import datetime, timezone
import logging
from domain.device_registry.models import DeviceMapping, MappingStatus, Device, EntityType
from domain.device_registry.validators import validate_mapping_conflict
from domain.device_registry.registry import DeviceRegistry
from domain.device_registry.base import BaseDeviceResolver

logger = logging.getLogger(__name__)


class DeviceMappingService(BaseDeviceResolver):
    """
    Manages the assignment of devices to FleetGuard entities.
    """
    def __init__(self, registry: DeviceRegistry):
        self._registry = registry
        self._mappings: List[DeviceMapping] = []

    def assign_device(self, device: Device, entity_type: EntityType, entity_id: str) -> DeviceMapping:
        """
        Assigns a device to an entity.
        Validates assignment rules before creating the mapping.
        """
        self.validate_assignments(device, entity_type, entity_id)
        
        mapping = DeviceMapping(
            device_id=device.device_id,
            entity_type=entity_type,
            entity_id=entity_id
        )
        self._mappings.append(mapping)
        logger.info(f"Assigned device {device.device_id} to {entity_type.value}:{entity_id}")
        return mapping

    def unassign_device(self, device_id: uuid.UUID) -> Optional[DeviceMapping]:
        """
        Deactivates an active mapping for a device.
        """
        for i, m in enumerate(self._mappings):
            if m.device_id == device_id and m.status == MappingStatus.ACTIVE:
                deactivated_mapping = m.model_copy(update={
                    "status": MappingStatus.INACTIVE,
                    "unassigned_at": datetime.now(timezone.utc)
                })
                self._mappings[i] = deactivated_mapping
                logger.info(f"Unassigned device {device_id} from {m.entity_type.value}:{m.entity_id}")
                return deactivated_mapping
        return None

    def resolve_device(self, provider: str, serial_number: str) -> Optional[Device]:
        """
        Resolves a hardware device from its provider-specific identifiers.
        """
        return self._registry.get_device(provider, serial_number)

    def resolve_mapping(self, device_id: uuid.UUID) -> Optional[DeviceMapping]:
        """
        Returns the active mapping for a given device, if any.
        """
        for m in self._mappings:
            if m.device_id == device_id and m.status == MappingStatus.ACTIVE:
                return m
        return None

    def validate_assignments(self, device: Device, entity_type: EntityType, entity_id: str) -> None:
        """
        Validates whether a device can be mapped to a specific entity.
        Raises ValueError if conflicts are found.
        """
        all_devices = self._registry.get_all_devices()
        validate_mapping_conflict(device, entity_type, entity_id, self._mappings, all_devices)
