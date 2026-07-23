"""
Assignment Management Domain - Aggregate Root
"""

from typing import List, Tuple, Optional
from datetime import datetime, timezone

from domain.assignment.models import Assignment, AssignmentStatus
from domain.assignment.events import (
    DomainEvent,
    AssignmentCreated,
    AssignmentActivated,
    AssignmentSuspended,
    AssignmentEnded,
    AssignmentTransferred
)
from domain.assignment.errors import InvalidAssignmentState
from domain.assignment.validators import validate_state_transition


class AssignmentAggregate:
    """
    Enforces domain invariants and coordinates state transitions for Assignments.
    """

    @classmethod
    def create_assignment(cls, assignment: Assignment) -> Tuple[Assignment, List[DomainEvent]]:
        """
        Creates a new assignment and registers its creation event.
        """
        if assignment.status != AssignmentStatus.PENDING:
            assignment = assignment.model_copy(update={"status": AssignmentStatus.PENDING})

        event = AssignmentCreated(
            assignment_id=assignment.assignment_id,
            organization_id=assignment.organization_id,
            assignment_type=assignment.assignment_type,
            source_entity_id=assignment.source_entity_id,
            target_entity_id=assignment.target_entity_id,
            effective_from=assignment.effective_from,
            metadata=assignment.metadata
        )
        return assignment, [event]

    @classmethod
    def activate_assignment(cls, assignment: Assignment, reason: Optional[str] = None) -> Tuple[Assignment, List[DomainEvent]]:
        if assignment.status == AssignmentStatus.ACTIVE:
            return assignment, []
            
        validate_state_transition(assignment.status, AssignmentStatus.ACTIVE)
        
        updated = assignment.model_copy(update={"status": AssignmentStatus.ACTIVE})
        event = AssignmentActivated(assignment_id=assignment.assignment_id, reason=reason)
        return updated, [event]

    @classmethod
    def suspend_assignment(cls, assignment: Assignment, reason: Optional[str] = None) -> Tuple[Assignment, List[DomainEvent]]:
        if assignment.status == AssignmentStatus.SUSPENDED:
            return assignment, []
            
        validate_state_transition(assignment.status, AssignmentStatus.SUSPENDED)
        
        updated = assignment.model_copy(update={"status": AssignmentStatus.SUSPENDED})
        event = AssignmentSuspended(assignment_id=assignment.assignment_id, reason=reason)
        return updated, [event]

    @classmethod
    def end_assignment(cls, assignment: Assignment, reason: Optional[str] = None) -> Tuple[Assignment, List[DomainEvent]]:
        if assignment.status == AssignmentStatus.ENDED:
            return assignment, []
            
        validate_state_transition(assignment.status, AssignmentStatus.ENDED)
        
        now = datetime.now(timezone.utc)
        updated = assignment.model_copy(update={
            "status": AssignmentStatus.ENDED,
            "ended_at": now,
            "effective_until": now
        })
        event = AssignmentEnded(assignment_id=assignment.assignment_id, ended_at=now, reason=reason)
        return updated, [event]

    @classmethod
    def transfer_assignment(
        cls, 
        current_assignment: Assignment, 
        new_assignment: Assignment,
        reason: Optional[str] = None
    ) -> Tuple[Assignment, Assignment, List[DomainEvent]]:
        """
        Ends the current assignment and creates a new one, emitting a transfer event.
        Returns (ended_assignment, new_assignment, events).
        """
        if current_assignment.source_entity_id != new_assignment.source_entity_id:
            raise InvalidAssignmentState("Transfers must be for the same source entity.")
            
        ended_assignment, end_events = cls.end_assignment(current_assignment, reason=f"Transferred to {new_assignment.target_entity_id}")
        created_assignment, create_events = cls.create_assignment(new_assignment)
        
        transfer_event = AssignmentTransferred(
            old_assignment_id=current_assignment.assignment_id,
            new_assignment_id=new_assignment.assignment_id,
            source_entity_id=current_assignment.source_entity_id,
            old_target_entity_id=current_assignment.target_entity_id,
            new_target_entity_id=new_assignment.target_entity_id,
            reason=reason
        )
        
        all_events = end_events + create_events + [transfer_event]
        return ended_assignment, created_assignment, all_events
