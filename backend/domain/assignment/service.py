"""
Assignment Management Domain - Service
"""

import uuid
from typing import List, Optional

from domain.assignment.models import Assignment, AssignmentStatus
from domain.assignment.aggregate import AssignmentAggregate
from domain.assignment.repository import BaseAssignmentRepository
from domain.assignment.errors import AssignmentNotFound, AssignmentValidationFailed
from domain.assignment.validators import validate_driver_assignment_conflict


class AssignmentService:
    """
    Application service orchestrating the Assignment domain.
    """

    def __init__(self, repository: BaseAssignmentRepository):
        self._repository = repository

    def create_assignment(self, assignment: Assignment) -> Assignment:
        # Validate conflict
        active_assignments = self._repository.find_active_assignments(assignment.organization_id)
        validate_driver_assignment_conflict(
            assignment.source_entity_id, 
            assignment.target_entity_id, 
            active_assignments
        )
        
        # Vehicle & Driver existence validation would typically be done here 
        # by calling interfaces to Vehicle and Driver domains, 
        # but to keep boundaries clean, we assume the API/Gateway layer validates IDs 
        # before passing them, or we could inject cross-domain validators.

        new_assignment, events = AssignmentAggregate.create_assignment(assignment)
        self._repository.create(new_assignment)
        
        # TODO: Publish events via EventBus
        
        return new_assignment

    def activate_assignment(self, assignment_id: uuid.UUID, reason: Optional[str] = None) -> Assignment:
        assignment = self._get_assignment(assignment_id)
        
        # Validate conflict before activation
        active_assignments = self._repository.find_active_assignments(assignment.organization_id)
        validate_driver_assignment_conflict(
            assignment.source_entity_id, 
            assignment.target_entity_id, 
            active_assignments
        )

        updated_assignment, events = AssignmentAggregate.activate_assignment(assignment, reason)
        self._repository.update(updated_assignment)
        return updated_assignment

    def suspend_assignment(self, assignment_id: uuid.UUID, reason: Optional[str] = None) -> Assignment:
        assignment = self._get_assignment(assignment_id)
        updated_assignment, events = AssignmentAggregate.suspend_assignment(assignment, reason)
        self._repository.update(updated_assignment)
        return updated_assignment

    def end_assignment(self, assignment_id: uuid.UUID, reason: Optional[str] = None) -> Assignment:
        assignment = self._get_assignment(assignment_id)
        updated_assignment, events = AssignmentAggregate.end_assignment(assignment, reason)
        self._repository.update(updated_assignment)
        return updated_assignment

    def transfer_assignment(self, current_assignment_id: uuid.UUID, new_target_entity_id: str, reason: Optional[str] = None) -> Assignment:
        current = self._get_assignment(current_assignment_id)
        
        if current.status != AssignmentStatus.ACTIVE:
            raise AssignmentValidationFailed("Can only transfer active assignments.")
            
        new_assignment = current.model_copy(
            update={
                "assignment_id": uuid.uuid4(),
                "target_entity_id": new_target_entity_id,
                "status": AssignmentStatus.PENDING
            },
            deep=True
        )
        
        # Validate conflict on new target
        active_assignments = self._repository.find_active_assignments(current.organization_id)
        validate_driver_assignment_conflict(
            new_assignment.source_entity_id, 
            new_assignment.target_entity_id, 
            [a for a in active_assignments if a.assignment_id != current.assignment_id]
        )

        ended_current, created_new, events = AssignmentAggregate.transfer_assignment(current, new_assignment, reason)
        
        self._repository.update(ended_current)
        self._repository.create(created_new)
        return created_new

    def _get_assignment(self, assignment_id: uuid.UUID) -> Assignment:
        assignment = self._repository.find_by_id(assignment_id)
        if not assignment:
            raise AssignmentNotFound(f"Assignment with ID {assignment_id} not found.")
        return assignment
