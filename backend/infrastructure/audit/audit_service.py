"""
Audit Framework - Service
"""

import uuid
from typing import List, Optional
from infrastructure.audit.models import AuditRecord
from infrastructure.audit.repository import BaseAuditRepository
from infrastructure.audit.tracking import AuditTracker
from infrastructure.audit.validators import validate_audit_record

class AuditService:
    """
    Main interface for business domains to interact with the audit framework.
    """
    def __init__(self, repository: BaseAuditRepository, tracker: AuditTracker):
        self.repository = repository
        self.tracker = tracker

    def record(self, audit_record: AuditRecord) -> None:
        """
        Validates and records a single audit entry.
        """
        validate_audit_record(audit_record)
        self.repository.save(audit_record)

    def record_batch(self, audit_records: List[AuditRecord]) -> None:
        """
        Validates and records a batch of audit entries.
        """
        for record in audit_records:
            validate_audit_record(record)
        self.repository.save_batch(audit_records)

    def get_record(self, audit_id: uuid.UUID) -> Optional[AuditRecord]:
        """
        Retrieves a specific audit record by ID.
        """
        return self.repository.find_by_id(audit_id)

    def get_entity_history(self, entity_type: str, entity_id: str) -> List[AuditRecord]:
        """
        Retrieves the chronological audit history for a specific entity.
        """
        return self.tracker.get_history_for_entity(entity_type, entity_id)
