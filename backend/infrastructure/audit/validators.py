"""
Audit Framework - Validators
"""

from datetime import datetime
from typing import Any
from infrastructure.audit.errors import InvalidAuditRecord
from infrastructure.audit.models import AuditRecord

def validate_audit_record(record: AuditRecord) -> None:
    """
    Validates structural integrity of an audit record.
    """
    if not record.event.event_name.strip():
        raise InvalidAuditRecord("Event name cannot be empty.")
        
    if not record.event.entity_type.strip():
        raise InvalidAuditRecord("Entity type cannot be empty.")
        
    if not record.event.entity_id.strip():
        raise InvalidAuditRecord("Entity ID cannot be empty.")
        
    if not record.event.actor_type.strip():
        raise InvalidAuditRecord("Actor type cannot be empty.")
        
    # Validation passes if no exceptions raised
