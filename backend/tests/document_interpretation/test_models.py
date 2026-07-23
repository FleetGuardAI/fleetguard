import unittest
from datetime import datetime, timezone
from pydantic import ValidationError
from domain.document_interpretation.models import BusinessDocumentType, ValidationIssue, InterpretationResult
from domain.document_interpretation.events import FuelPurchaseRecorded

class TestDocumentInterpretationModels(unittest.TestCase):
    def test_validation_issue_immutability(self):
        issue = ValidationIssue(field_name="total_amount", severity="ERROR", error_code="MISSING", message="msg")
        with self.assertRaises(ValidationError):
            issue.field_name = "other"

    def test_interpretation_result_immutability(self):
        res = InterpretationResult(
            structured_document_id="doc-123",
            business_document_type=BusinessDocumentType.FUEL_RECEIPT,
            operational_events=[]
        )
        with self.assertRaises(ValidationError):
            res.structured_document_id = "doc-456"

    def test_operational_event_immutability(self):
        event = FuelPurchaseRecorded(
            source_document_id="doc-123",
            fuel_quantity=10.0,
            total_amount=500.0,
            purchase_date="2026-07-20"
        )
        with self.assertRaises(ValidationError):
            event.total_amount = 600.0
