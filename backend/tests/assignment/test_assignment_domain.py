import unittest
import uuid
from datetime import datetime, timezone

from domain.assignment.models import Assignment, AssignmentType, AssignmentStatus
from domain.assignment.service import AssignmentService
from domain.assignment.repository import InMemoryAssignmentRepository
from domain.assignment.errors import InvalidAssignmentState, AssignmentConflictError, AssignmentNotFound

class TestAssignmentDomain(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryAssignmentRepository()
        self.service = AssignmentService(self.repo)
        self.org_id = uuid.uuid4()

    def test_create_and_activate_assignment(self):
        assignment = Assignment(
            organization_id=self.org_id,
            assignment_type=AssignmentType.DRIVER_TO_VEHICLE,
            source_entity_id="drv-1",
            target_entity_id="veh-1",
            created_by="system"
        )
        
        created = self.service.create_assignment(assignment)
        self.assertEqual(created.status, AssignmentStatus.PENDING)
        
        activated = self.service.activate_assignment(created.assignment_id, "Start shift")
        self.assertEqual(activated.status, AssignmentStatus.ACTIVE)
        
        # Verify repository state
        active = self.repo.find_active_assignments(self.org_id)
        self.assertEqual(len(active), 1)
        
    def test_prevent_driver_double_assignment(self):
        # Driver 1 to Vehicle 1
        a1 = Assignment(
            organization_id=self.org_id,
            assignment_type=AssignmentType.DRIVER_TO_VEHICLE,
            source_entity_id="drv-1",
            target_entity_id="veh-1",
            created_by="system"
        )
        c1 = self.service.create_assignment(a1)
        self.service.activate_assignment(c1.assignment_id)
        
        # Driver 1 to Vehicle 2 (Conflict)
        a2 = Assignment(
            organization_id=self.org_id,
            assignment_type=AssignmentType.DRIVER_TO_VEHICLE,
            source_entity_id="drv-1",
            target_entity_id="veh-2",
            created_by="system"
        )
        
        with self.assertRaises(AssignmentConflictError):
            c2 = self.service.create_assignment(a2)
            self.service.activate_assignment(c2.assignment_id)

    def test_transfer_assignment(self):
        a1 = Assignment(
            organization_id=self.org_id,
            assignment_type=AssignmentType.DRIVER_TO_VEHICLE,
            source_entity_id="drv-1",
            target_entity_id="veh-1",
            created_by="system"
        )
        c1 = self.service.create_assignment(a1)
        self.service.activate_assignment(c1.assignment_id)
        
        # Transfer drv-1 to veh-2
        new_assignment = self.service.transfer_assignment(c1.assignment_id, "veh-2", "Vehicle breakdown")
        
        self.assertEqual(new_assignment.status, AssignmentStatus.PENDING)
        self.assertEqual(new_assignment.target_entity_id, "veh-2")
        
        old_assignment = self.repo.find_by_id(c1.assignment_id)
        self.assertEqual(old_assignment.status, AssignmentStatus.ENDED)

if __name__ == "__main__":
    unittest.main()
