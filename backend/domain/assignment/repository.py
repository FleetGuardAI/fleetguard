"""
Assignment Management Domain - Repository
"""

import abc
import uuid
from typing import List, Optional
from domain.assignment.models import Assignment, AssignmentStatus


class BaseAssignmentRepository(abc.ABC):
    @abc.abstractmethod
    def create(self, assignment: Assignment) -> None:
        pass
        
    @abc.abstractmethod
    def update(self, assignment: Assignment) -> None:
        pass
        
    @abc.abstractmethod
    def find_by_id(self, assignment_id: uuid.UUID) -> Optional[Assignment]:
        pass

    @abc.abstractmethod
    def list(self) -> List[Assignment]:
        pass

    @abc.abstractmethod
    def search(self, **kwargs) -> List[Assignment]:
        pass

    @abc.abstractmethod
    def find_active_assignments(self, organization_id: uuid.UUID) -> List[Assignment]:
        pass
        
    @abc.abstractmethod
    def find_assignments_by_vehicle(self, vehicle_id: str) -> List[Assignment]:
        pass
        
    @abc.abstractmethod
    def find_assignments_by_driver(self, driver_id: str) -> List[Assignment]:
        pass

    @abc.abstractmethod
    def exists(self, assignment_id: uuid.UUID) -> bool:
        pass


class InMemoryAssignmentRepository(BaseAssignmentRepository):
    def __init__(self):
        self._assignments = {}

    def create(self, assignment: Assignment) -> None:
        self._assignments[assignment.assignment_id] = assignment
        
    def update(self, assignment: Assignment) -> None:
        self._assignments[assignment.assignment_id] = assignment
        
    def find_by_id(self, assignment_id: uuid.UUID) -> Optional[Assignment]:
        return self._assignments.get(assignment_id)
        
    def list(self) -> List[Assignment]:
        return list(self._assignments.values())

    def search(self, **kwargs) -> List[Assignment]:
        results = list(self._assignments.values())
        if "status" in kwargs:
            results = [a for a in results if a.status == kwargs["status"]]
        if "assignment_type" in kwargs:
            results = [a for a in results if a.assignment_type == kwargs["assignment_type"]]
        if "organization_id" in kwargs:
            results = [a for a in results if a.organization_id == kwargs["organization_id"]]
        if "source_entity_id" in kwargs:
            results = [a for a in results if a.source_entity_id == kwargs["source_entity_id"]]
        if "target_entity_id" in kwargs:
            results = [a for a in results if a.target_entity_id == kwargs["target_entity_id"]]
        return results

    def find_active_assignments(self, organization_id: uuid.UUID) -> List[Assignment]:
        return [
            a for a in self._assignments.values() 
            if a.organization_id == organization_id and a.status == AssignmentStatus.ACTIVE
        ]

    def find_assignments_by_vehicle(self, vehicle_id: str) -> List[Assignment]:
        return [a for a in self._assignments.values() if a.target_entity_id == vehicle_id]

    def find_assignments_by_driver(self, driver_id: str) -> List[Assignment]:
        return [a for a in self._assignments.values() if a.source_entity_id == driver_id]

    def exists(self, assignment_id: uuid.UUID) -> bool:
        return assignment_id in self._assignments
