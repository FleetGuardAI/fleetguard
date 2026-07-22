import unittest
from datetime import datetime, timezone, timedelta
from infrastructure.audit.repository import InMemoryAuditRepository
from infrastructure.audit.tracking import AuditTracker
from infrastructure.audit.models import AuditRecord, AuditEvent, AuditCategory, AuditSeverity

class TestAuditTracker(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryAuditRepository()
        self.tracker = AuditTracker(self.repo)
        
        now = datetime.now(timezone.utc)
        
        self.r1 = AuditRecord(event=AuditEvent(
            timestamp=now - timedelta(minutes=10),
            category=AuditCategory.USER,
            severity=AuditSeverity.INFO,
            event_name="login",
            entity_type="user",
            entity_id="u1",
            actor_type="user",
            actor_id="u1",
            correlation_id="c1"
        ))
        
        self.r2 = AuditRecord(event=AuditEvent(
            timestamp=now - timedelta(minutes=5),
            category=AuditCategory.USER,
            severity=AuditSeverity.WARNING,
            event_name="failed_login",
            entity_type="user",
            entity_id="u1",
            actor_type="user",
            actor_id="u1",
            correlation_id="c2"
        ))
        
        self.repo.save_batch([self.r1, self.r2])
        
    def test_get_history_for_entity(self):
        history = self.tracker.get_history_for_entity("user", "u1")
        self.assertEqual(len(history), 2)
        # Should be chronologically sorted
        self.assertEqual(history[0].event.event_name, "login")
        self.assertEqual(history[1].event.event_name, "failed_login")
        
    def test_filter_records(self):
        # By category
        filtered = self.tracker.filter_records(category="USER")
        self.assertEqual(len(filtered), 2)
        
        # By severity
        filtered_sev = self.tracker.filter_records(severity="WARNING")
        self.assertEqual(len(filtered_sev), 1)
        self.assertEqual(filtered_sev[0].event.event_name, "failed_login")
        
        # By correlation
        filtered_corr = self.tracker.filter_records(correlation_id="c1")
        self.assertEqual(len(filtered_corr), 1)
        self.assertEqual(filtered_corr[0].event.event_name, "login")
