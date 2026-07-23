import unittest
from infrastructure.documents.models import StructuredDocument, DocumentFamily, ExtractedField
from domain.document_interpretation.validators import validate_required_fields

class TestValidators(unittest.TestCase):
    def test_validate_required_fields_success(self):
        doc = StructuredDocument(
            attachment_id="att-1",
            document_family=DocumentFamily.INVOICE,
            extraction_method="ocr",
            extracted_text="text",
            structured_fields=[
                ExtractedField(name="total_amount", value="100.0"),
                ExtractedField(name="date", value="2026-07-20")
            ]
        )
        issues = validate_required_fields(doc, ["total_amount", "date"])
        self.assertEqual(len(issues), 0)

    def test_validate_required_fields_missing(self):
        doc = StructuredDocument(
            attachment_id="att-1",
            document_family=DocumentFamily.INVOICE,
            extraction_method="ocr",
            extracted_text="text",
            structured_fields=[
                ExtractedField(name="total_amount", value="100.0")
            ]
        )
        issues = validate_required_fields(doc, ["total_amount", "date"])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field_name, "date")
        self.assertEqual(issues[0].error_code, "MISSING_REQUIRED_FIELD")

    def test_validate_required_fields_empty(self):
        doc = StructuredDocument(
            attachment_id="att-1",
            document_family=DocumentFamily.INVOICE,
            extraction_method="ocr",
            extracted_text="text",
            structured_fields=[
                ExtractedField(name="total_amount", value="100.0"),
                ExtractedField(name="date", value="")
            ]
        )
        issues = validate_required_fields(doc, ["total_amount", "date"])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].field_name, "date")
        self.assertEqual(issues[0].error_code, "EMPTY_REQUIRED_FIELD")
