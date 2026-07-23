import unittest
from infrastructure.audit.validators import validate_audit_record
from infrastructure.audit.errors import InvalidAuditRecord
from infrastructure.audit.models import AuditRecord, AuditEvent, AuditCategory

class TestAuditValidators(unittest.TestCase):
    def test_valid_record(self):
        event = AuditEvent(
            category=AuditCategory.SYSTEM,
            event_name="startup",
            entity_type="system",
            entity_id="host-1",
            actor_type="system"
        )
        record = AuditRecord(event=event)
        # Should not raise
        validate_audit_record(record)
        
    def test_missing_event_name(self):
        event = AuditEvent(
            category=AuditCategory.SYSTEM,
            event_name=" ",
            entity_type="system",
            entity_id="host-1",
            actor_type="system"
        )
        record = AuditRecord(event=event)
        with self.assertRaises(InvalidAuditRecord):
            validate_audit_record(record)
