import unittest
from datetime import datetime, timezone
from pydantic import ValidationError
from infrastructure.documents.models import DocumentFamily, ExtractedField, ExtractionDiagnostics, StructuredDocument, DocumentProcessingStatus, DocumentProcessingResult

class TestDocumentModels(unittest.TestCase):
    def test_extracted_field_immutability(self):
        field = ExtractedField(name="test", value=123, confidence=0.9, source_info="regex")
        with self.assertRaises(ValidationError):
            field.value = 456

    def test_diagnostics_immutability(self):
        diag = ExtractionDiagnostics(engine="test", processing_time_ms=10.0)
        with self.assertRaises(ValidationError):
            diag.engine = "new"

    def test_structured_document_immutability(self):
        doc = StructuredDocument(
            attachment_id="att-123",
            document_family=DocumentFamily.INVOICE,
            extraction_method="ocr",
            extracted_text="hello"
        )
        with self.assertRaises(ValidationError):
            doc.extracted_text = "new"

    def test_processing_result_immutability(self):
        res = DocumentProcessingResult(
            processing_status=DocumentProcessingStatus.SUCCESS,
            execution_time=0.5
        )
        with self.assertRaises(ValidationError):
            res.execution_time = 0.1
