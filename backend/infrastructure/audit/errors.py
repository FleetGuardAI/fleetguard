"""
Audit Framework - Errors
"""

class AuditError(Exception):
    """Base exception for Audit Framework errors."""
    pass

class AuditRecordNotFound(AuditError):
    pass

class InvalidAuditRecord(AuditError):
    pass

class InvalidAuditQuery(AuditError):
    pass
