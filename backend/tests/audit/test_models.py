import unittest
from pydantic import ValidationError
from infrastructure.audit.models import AuditRecord, AuditEvent, AuditCategory, AuditSeverity, EntityChange

class TestAuditModels(unittest.TestCase):
    def test_job_immutability(self):
        event = AuditEvent(
            category=AuditCategory.SYSTEM,
            event_name="startup",
            entity_type="system",
            entity_id="host-1",
            actor_type="system"
        )
        record = AuditRecord(event=event)
        
        with self.assertRaises(ValidationError):
            record.event = event # frozen
            
        with self.assertRaises(ValidationError):
            event.event_name = "shutdown" # frozen
