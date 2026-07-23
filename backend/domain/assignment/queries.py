"""
Assignment Management Domain - Query Layer
"""

import uuid
from typing import List, Optional
from domain.assignment.repository import BaseAssignmentRepository
from domain.assignment.projections import (
    AssignmentSummary,
    VehicleAssignmentSummary,
    DriverAssignmentSummary
)
from domain.assignment.models import AssignmentStatus, AssignmentType


class AssignmentQueryService:
    """
    Provides optimized read models for the Assignment domain.
    """
    def __init__(self, repository: BaseAssignmentRepository):
        self._repository = repository

    def active_vehicle_assignments(self, organization_id: uuid.UUID) -> List[VehicleAssignmentSummary]:
        active = self._repository.find_active_assignments(organization_id)
        
        summaries = []
        for assignment in active:
            if assignment.assignment_type == AssignmentType.DRIVER_TO_VEHICLE:
                summaries.append(VehicleAssignmentSummary(
                    vehicle_id=assignment.target_entity_id,
                    active_driver_id=assignment.source_entity_id,
                    assignment_id=assignment.assignment_id,
                    effective_from=assignment.effective_from
                ))
        return summaries

    def active_driver_assignments(self, organization_id: uuid.UUID) -> List[DriverAssignmentSummary]:
        active = self._repository.find_active_assignments(organization_id)
        
        summaries = []
        for assignment in active:
            if assignment.assignment_type == AssignmentType.DRIVER_TO_VEHICLE:
                summaries.append(DriverAssignmentSummary(
                    driver_id=assignment.source_entity_id,
                    active_vehicle_id=assignment.target_entity_id,
                    assignment_id=assignment.assignment_id,
                    effective_from=assignment.effective_from
                ))
        return summaries

    def assignment_history(self, source_entity_id: str = None, target_entity_id: str = None) -> List[AssignmentSummary]:
        results = self._repository.list()
        
        if source_entity_id:
            results = [a for a in results if a.source_entity_id == source_entity_id]
        if target_entity_id:
            results = [a for a in results if a.target_entity_id == target_entity_id]
            
        return [
            AssignmentSummary(
                assignment_id=a.assignment_id,
                assignment_type=a.assignment_type,
                source_entity_id=a.source_entity_id,
                target_entity_id=a.target_entity_id,
                status=a.status,
                effective_from=a.effective_from,
                effective_until=a.effective_until
            ) for a in results
        ]
