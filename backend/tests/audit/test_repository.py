import unittest
from infrastructure.audit.repository import InMemoryAuditRepository
from infrastructure.audit.models import AuditRecord, AuditEvent, AuditCategory

class TestAuditRepository(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryAuditRepository()
        
    def test_save_and_find(self):
        event = AuditEvent(
            category=AuditCategory.SYSTEM,
            event_name="startup",
            entity_type="system",
            entity_id="host-1",
            actor_type="system",
            correlation_id="corr-123"
        )
        record = AuditRecord(event=event)
        
        self.repo.save(record)
        
        # Test find_by_id
        found = self.repo.find_by_id(event.audit_id)
        self.assertIsNotNone(found)
        self.assertEqual(found.event.audit_id, event.audit_id)
        
        # Test find_by_entity
        entity_records = self.repo.find_by_entity("system", "host-1")
        self.assertEqual(len(entity_records), 1)
        
        # Test find_by_category
        cat_records = self.repo.find_by_category("SYSTEM")
        self.assertEqual(len(cat_records), 1)
        
        # Test find_by_correlation
        corr_records = self.repo.find_by_correlation("corr-123")
        self.assertEqual(len(corr_records), 1)
