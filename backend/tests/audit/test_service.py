import unittest
from infrastructure.audit.repository import InMemoryAuditRepository
from infrastructure.audit.tracking import AuditTracker
from infrastructure.audit.audit_service import AuditService
from infrastructure.audit.models import AuditRecord, AuditEvent, AuditCategory
from infrastructure.audit.errors import InvalidAuditRecord

class TestAuditService(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryAuditRepository()
        self.tracker = AuditTracker(self.repo)
        self.service = AuditService(self.repo, self.tracker)
        
    def test_record_valid(self):
        event = AuditEvent(
            category=AuditCategory.SYSTEM,
            event_name="startup",
            entity_type="system",
            entity_id="host-1",
            actor_type="system"
        )
        record = AuditRecord(event=event)
        
        self.service.record(record)
        found = self.service.get_record(event.audit_id)
        self.assertIsNotNone(found)
        
    def test_record_invalid(self):
        event = AuditEvent(
            category=AuditCategory.SYSTEM,
            event_name="",
            entity_type="system",
            entity_id="host-1",
            actor_type="system"
        )
        record = AuditRecord(event=event)
        
        with self.assertRaises(InvalidAuditRecord):
            self.service.record(record)
