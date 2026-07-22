import unittest
from domain.document_interpretation.executor import DocumentInterpretationExecutor
from domain.document_interpretation.registry import DocumentInterpreterRegistry
from domain.document_interpretation.interpreters.fuel_receipt import FuelReceiptInterpreter
from domain.document_interpretation.models import BusinessDocumentType
from infrastructure.documents.models import StructuredDocument, DocumentFamily, ExtractedField

class TestExecutor(unittest.TestCase):
    def setUp(self):
        self.registry = DocumentInterpreterRegistry()
        self.registry.register(FuelReceiptInterpreter)
        self.executor = DocumentInterpretationExecutor(self.registry)

    def test_process_document_success(self):
        doc = StructuredDocument(
            attachment_id="att-1",
            document_family=DocumentFamily.RECEIPT,
            extraction_method="ocr",
            extracted_text="FUEL BILL",
            structured_fields=[
                ExtractedField(name="total_paid", value="100.0"),
                ExtractedField(name="date", value="2026-07-20")
            ]
        )
        result = self.executor.process_document(doc)
        self.assertEqual(result.business_document_type, BusinessDocumentType.FUEL_RECEIPT)
        self.assertEqual(len(result.validation_results), 0)
        self.assertEqual(len(result.operational_events), 1)

    def test_process_document_validation_failure(self):
        doc = StructuredDocument(
            attachment_id="att-1",
            document_family=DocumentFamily.RECEIPT,
            extraction_method="ocr",
            extracted_text="FUEL BILL",
            structured_fields=[] # Missing required fields
        )
        result = self.executor.process_document(doc)
        self.assertEqual(result.business_document_type, BusinessDocumentType.FUEL_RECEIPT)
        self.assertEqual(len(result.operational_events), 0) # No events due to validation error
        self.assertTrue(len(result.validation_results) > 0)
        
    def test_no_interpreter_found(self):
        doc = StructuredDocument(
            attachment_id="att-1",
            document_family=DocumentFamily.CERTIFICATE,
            extraction_method="ocr",
            extracted_text="UNKNOWN CERTIFICATE",
            structured_fields=[]
        )
        result = self.executor.process_document(doc)
        self.assertEqual(result.business_document_type, BusinessDocumentType.UNKNOWN)
        self.assertEqual(result.validation_results[0].error_code, "NO_INTERPRETER_FOUND")
