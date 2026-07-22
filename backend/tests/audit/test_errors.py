import unittest
from infrastructure.audit.errors import AuditError, AuditRecordNotFound, InvalidAuditRecord, InvalidAuditQuery

class TestAuditErrors(unittest.TestCase):
    def test_error_hierarchy(self):
        self.assertTrue(issubclass(AuditRecordNotFound, AuditError))
        self.assertTrue(issubclass(InvalidAuditRecord, AuditError))
        self.assertTrue(issubclass(InvalidAuditQuery, AuditError))
