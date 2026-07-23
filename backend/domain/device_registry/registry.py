"""
Device Registry & Mapping Framework - Registry
"""

from typing import List, Optional, Dict
import logging
from domain.device_registry.models import Device
from domain.device_registry.validators import validate_duplicate_device


logger = logging.getLogger(__name__)


class DeviceRegistry:
    """
    Central registry for managing hardware devices.
    """
    def __init__(self):
        # In-memory storage for demonstration/testing. 
        # In a real system, this would be backed by a database repository.
        self._devices: List[Device] = []

    def register_device(self, device: Device) -> Device:
        """
        Registers a new hardware device.
        """
        validate_duplicate_device(device.provider, device.serial_number, self._devices)
        self._devices.append(device)
        logger.debug(f"Registered device: {device.device_id} ({device.provider}:{device.serial_number})")
        return device

    def get_device(self, provider: str, serial_number: str) -> Optional[Device]:
        """
        Retrieves a device by provider and serial number.
        """
        for d in self._devices:
            if d.provider == provider and d.serial_number == serial_number:
                return d
        return None
        
    def get_all_devices(self) -> List[Device]:
        """
        Returns all registered devices.
        """
        return list(self._devices)

    def update_metadata(self, provider: str, serial_number: str, metadata: Dict) -> Optional[Device]:
        """
        Updates the metadata for an existing device.
        Because models are frozen, we create a new instance and replace it.
        """
        for i, d in enumerate(self._devices):
            if d.provider == provider and d.serial_number == serial_number:
                # Create a new dictionary extending the old metadata
                new_metadata = dict(d.metadata)
                new_metadata.update(metadata)
                
                # Replace the old device with a new copy containing updated metadata
                updated_device = d.model_copy(update={"metadata": new_metadata})
                self._devices[i] = updated_device
                return updated_device
        return None
