"""
Driver Management Domain - Validators
"""

from domain.driver.models import DriverStatus
from domain.driver.errors import InvalidDriverState

def validate_state_transition(current: DriverStatus, target: DriverStatus) -> None:
    """
    Validates if a state transition is legal.
    """
    if current == target:
        return
        
    if current == DriverStatus.RETIRED:
        raise InvalidDriverState("Cannot change state of a RETIRED driver.")
        
    if current == DriverStatus.ARCHIVED and target != DriverStatus.ARCHIVED:
        raise InvalidDriverState("Cannot reactivate an ARCHIVED driver directly.")
        
    # Other transitions (e.g. ACTIVE -> SUSPENDED) are generally allowed by the aggregate, 
    # but specific rules could be expanded here.
