"""
Assignment Management Domain - Validators
"""

from typing import List, Optional
from domain.assignment.models import Assignment, AssignmentStatus, AssignmentType
from domain.assignment.errors import InvalidAssignmentState, AssignmentConflictError, AssignmentValidationFailed


def validate_state_transition(current: AssignmentStatus, target: AssignmentStatus) -> None:
    """
    Validates if an assignment can transition from current to target status.
    """
    valid_transitions = {
        AssignmentStatus.PENDING: [AssignmentStatus.ACTIVE, AssignmentStatus.ENDED],
        AssignmentStatus.ACTIVE: [AssignmentStatus.SUSPENDED, AssignmentStatus.ENDED],
        AssignmentStatus.SUSPENDED: [AssignmentStatus.ACTIVE, AssignmentStatus.ENDED],
        AssignmentStatus.ENDED: []  # Terminal state
    }
    
    if target not in valid_transitions.get(current, []):
        raise InvalidAssignmentState(f"Cannot transition assignment from {current} to {target}.")


def validate_driver_assignment_conflict(
    driver_id: str, 
    vehicle_id: str, 
    active_assignments: List[Assignment]
) -> None:
    """
    Validates that a driver does not have multiple active assignments,
    and a vehicle does not have multiple active drivers.
    """
    for assignment in active_assignments:
        if assignment.status != AssignmentStatus.ACTIVE:
            continue
            
        if assignment.assignment_type == AssignmentType.DRIVER_TO_VEHICLE:
            if assignment.source_entity_id == driver_id and assignment.target_entity_id != vehicle_id:
                raise AssignmentConflictError(
                    f"Driver {driver_id} is already actively assigned to vehicle {assignment.target_entity_id}."
                )
            if assignment.target_entity_id == vehicle_id and assignment.source_entity_id != driver_id:
                raise AssignmentConflictError(
                    f"Vehicle {vehicle_id} already has an active driver {assignment.source_entity_id}."
                )
