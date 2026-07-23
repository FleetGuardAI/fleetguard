import unittest
from infrastructure.audit.repository import InMemoryAuditRepository
from infrastructure.audit.tracking import AuditTracker
from infrastructure.audit.audit_service import AuditService
from infrastructure.audit.models import AuditRecord, AuditEvent, AuditCategory, EntityChange

class TestAuditPipeline(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryAuditRepository()
        self.tracker = AuditTracker(self.repo)
        self.service = AuditService(self.repo, self.tracker)
        
    def test_correlation_workflow(self):
        # 1. System detects fuel anomaly
        corr_id = "investigation-99"
        
        evt1 = AuditEvent(
            category=AuditCategory.SYSTEM,
            event_name="anomaly_detected",
            entity_type="vehicle",
            entity_id="v1",
            actor_type="intelligence_engine",
            correlation_id=corr_id
        )
        self.service.record(AuditRecord(event=evt1))
        
        # 2. Notification sent
        evt2 = AuditEvent(
            category=AuditCategory.NOTIFICATION,
            event_name="notification_dispatched",
            entity_type="notification",
            entity_id="notif-1",
            actor_type="notification_service",
            correlation_id=corr_id
        )
        self.service.record(AuditRecord(event=evt2))
        
        # 3. User reviews and updates status
        evt3 = AuditEvent(
            category=AuditCategory.USER,
            event_name="status_updated",
            entity_type="investigation",
            entity_id="inv-1",
            actor_type="user",
            actor_id="u1",
            correlation_id=corr_id
        )
        changes = [
            EntityChange(field_name="status", previous_value="OPEN", new_value="CONFIRMED")
        ]
        self.service.record(AuditRecord(event=evt3, changes=changes))
        
        # Verify workflow reconstruction
        workflow_records = self.tracker.filter_records(correlation_id=corr_id)
        self.assertEqual(len(workflow_records), 3)
        
        # Verify chronological order
        self.assertEqual(workflow_records[0].event.event_name, "anomaly_detected")
        self.assertEqual(workflow_records[1].event.event_name, "notification_dispatched")
        self.assertEqual(workflow_records[2].event.event_name, "status_updated")
        
        # Verify changes were preserved
        self.assertEqual(len(workflow_records[2].changes), 1)
        self.assertEqual(workflow_records[2].changes[0].new_value, "CONFIRMED")
