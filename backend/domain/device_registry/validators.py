"""
Device Registry & Mapping Framework - Validators
"""

from typing import List, Optional
from domain.device_registry.models import Device, DeviceMapping, MappingStatus, DeviceType, EntityType


def validate_duplicate_device(provider: str, serial_number: str, existing_devices: List[Device]) -> None:
    """
    Validates that a provider and serial_number combination is unique.
    Raises ValueError if a duplicate is found.
    """
    for d in existing_devices:
        if d.provider == provider and d.serial_number == serial_number:
            raise ValueError(f"Device with provider '{provider}' and serial '{serial_number}' already exists.")


def validate_mapping_conflict(device: Device, 
                              entity_type: EntityType, 
                              entity_id: str, 
                              existing_mappings: List[DeviceMapping],
                              all_devices: List[Device]) -> None:
    """
    Validates assignment rules:
    1. A device can only have one ACTIVE mapping at a time.
    2. An entity can only have one ACTIVE mapping for a specific device type at a time 
       (e.g., a vehicle can only have one active GPS Tracker).
    """
    
    # Rule 1: A device can only have one active mapping.
    active_device_mappings = [m for m in existing_mappings if m.device_id == device.device_id and m.status == MappingStatus.ACTIVE]
    if active_device_mappings:
        raise ValueError(f"Device {device.device_id} already has an active mapping.")
        
    # Rule 2: An entity can only have one active mapping for a specific device type.
    active_entity_mappings = [
        m for m in existing_mappings 
        if m.entity_type == entity_type and m.entity_id == entity_id and m.status == MappingStatus.ACTIVE
    ]
    
    # We need to look up the device types of the currently mapped devices
    device_lookup = {d.device_id: d for d in all_devices}
    
    for m in active_entity_mappings:
        mapped_device = device_lookup.get(m.device_id)
        if mapped_device and mapped_device.device_type == device.device_type:
            raise ValueError(f"Entity {entity_type.value}:{entity_id} already has an active mapping for a {device.device_type.value}.")
