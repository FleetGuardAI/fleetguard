"""
Driver Management Domain - Aggregate Root
"""

import uuid
from typing import List, Tuple, Optional
from domain.driver.models import Driver, DriverStatus, DriverProfile, DriverPreferences
from domain.driver.value_objects import DriverLicence
from domain.driver.events import (
    DomainEvent,
    DriverRegistered,
    DriverActivated,
    DriverDeactivated,
    DriverSuspended,
    DriverArchived,
    DriverRetired,
    DriverProfileUpdated,
    DriverLicenceUpdated,
    DriverPreferencesUpdated
)
from domain.driver.validators import validate_state_transition


class DriverAggregate:
    """
    Enforces domain invariants and coordinates state transitions.
    """
    
    @classmethod
    def register_driver(cls, driver: Driver) -> Tuple[Driver, List[DomainEvent]]:
        """
        Creates a new driver and registers its creation event.
        """
        # Initial status must be INACTIVE
        if driver.status != DriverStatus.INACTIVE:
            driver = driver.model_copy(update={"status": DriverStatus.INACTIVE})
            
        event = DriverRegistered(
            driver_id=driver.driver_id,
            employee_code=driver.employee_code.value,
            organization_id=driver.organization_id,
            metadata=driver.metadata
        )
        return driver, [event]

    @classmethod
    def activate_driver(cls, driver: Driver, reason: Optional[str] = None) -> Tuple[Driver, List[DomainEvent]]:
        validate_state_transition(driver.status, DriverStatus.ACTIVE)
        if driver.status == DriverStatus.ACTIVE:
            return driver, []
            
        updated = driver.model_copy(update={"status": DriverStatus.ACTIVE})
        event = DriverActivated(driver_id=driver.driver_id, reason=reason)
        return updated, [event]

    @classmethod
    def deactivate_driver(cls, driver: Driver, reason: Optional[str] = None) -> Tuple[Driver, List[DomainEvent]]:
        validate_state_transition(driver.status, DriverStatus.INACTIVE)
        if driver.status == DriverStatus.INACTIVE:
            return driver, []
            
        updated = driver.model_copy(update={"status": DriverStatus.INACTIVE})
        event = DriverDeactivated(driver_id=driver.driver_id, reason=reason)
        return updated, [event]
        
    @classmethod
    def suspend_driver(cls, driver: Driver, reason: Optional[str] = None) -> Tuple[Driver, List[DomainEvent]]:
        validate_state_transition(driver.status, DriverStatus.SUSPENDED)
        if driver.status == DriverStatus.SUSPENDED:
            return driver, []
            
        updated = driver.model_copy(update={"status": DriverStatus.SUSPENDED})
        event = DriverSuspended(driver_id=driver.driver_id, reason=reason)
        return updated, [event]

    @classmethod
    def archive_driver(cls, driver: Driver, reason: Optional[str] = None) -> Tuple[Driver, List[DomainEvent]]:
        if driver.status == DriverStatus.ARCHIVED:
            return driver, []
            
        updated = driver.model_copy(update={"status": DriverStatus.ARCHIVED})
        event = DriverArchived(driver_id=driver.driver_id, reason=reason)
        return updated, [event]

    @classmethod
    def retire_driver(cls, driver: Driver, reason: Optional[str] = None) -> Tuple[Driver, List[DomainEvent]]:
        if driver.status == DriverStatus.RETIRED:
            return driver, []
            
        updated = driver.model_copy(update={"status": DriverStatus.RETIRED})
        event = DriverRetired(driver_id=driver.driver_id, reason=reason)
        return updated, [event]

    @classmethod
    def update_profile(cls, driver: Driver, profile: DriverProfile) -> Tuple[Driver, List[DomainEvent]]:
        validate_state_transition(driver.status, driver.status) # Just check if not retired
            
        updated = driver.model_copy(update={"profile": profile})
        event = DriverProfileUpdated(driver_id=driver.driver_id)
        return updated, [event]
        
    @classmethod
    def update_preferences(cls, driver: Driver, preferences: DriverPreferences) -> Tuple[Driver, List[DomainEvent]]:
        validate_state_transition(driver.status, driver.status)
            
        updated = driver.model_copy(update={"preferences": preferences})
        event = DriverPreferencesUpdated(driver_id=driver.driver_id)
        return updated, [event]
        
    @classmethod
    def update_licence(cls, driver: Driver, licence: DriverLicence) -> Tuple[Driver, List[DomainEvent]]:
        validate_state_transition(driver.status, driver.status)
            
        updated = driver.model_copy(update={"licence": licence})
        event = DriverLicenceUpdated(driver_id=driver.driver_id)
        return updated, [event]
