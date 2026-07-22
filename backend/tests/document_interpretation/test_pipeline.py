import unittest
from domain.document_interpretation.executor import DocumentInterpretationExecutor
from domain.document_interpretation.registry import DocumentInterpreterRegistry
from domain.document_interpretation.interpreters.tyre_invoice import TyreInvoiceInterpreter
from domain.document_interpretation.interpreters.unknown import UnknownInterpreter
from domain.document_interpretation.models import BusinessDocumentType
from infrastructure.documents.models import StructuredDocument, DocumentFamily, ExtractedField
from domain.document_interpretation.events import TyreReplacementRecorded

class TestDocumentInterpretationPipeline(unittest.TestCase):
    def setUp(self):
        self.registry = DocumentInterpreterRegistry()
        self.registry.register(TyreInvoiceInterpreter)
        self.registry.register(UnknownInterpreter) # Fallback
        self.executor = DocumentInterpretationExecutor(self.registry)

    def test_end_to_end_tyre_invoice(self):
        doc = StructuredDocument(
            attachment_id="att-1",
            document_family=DocumentFamily.INVOICE,
            extraction_method="ocr",
            extracted_text="TYRE REPLACEMENT INVOICE",
            structured_fields=[
                ExtractedField(name="total_amount", value="500.0"),
                ExtractedField(name="date", value="2026-07-20")
            ]
        )
        
        result = self.executor.process_document(doc)
        self.assertEqual(result.business_document_type, BusinessDocumentType.TYRE_INVOICE)
        self.assertEqual(len(result.validation_results), 0)
        self.assertEqual(len(result.operational_events), 1)
        
        event = result.operational_events[0]
        self.assertIsInstance(event, TyreReplacementRecorded)
        self.assertEqual(event.total_amount, 500.0)

    def test_end_to_end_fallback(self):
        doc = StructuredDocument(
            attachment_id="att-1",
            document_family=DocumentFamily.FORM,
            extraction_method="ocr",
            extracted_text="SOME UNKNOWN FORM",
            structured_fields=[]
        )
        
        result = self.executor.process_document(doc)
        self.assertEqual(result.business_document_type, BusinessDocumentType.UNKNOWN)
        self.assertEqual(len(result.validation_results), 0)
        self.assertEqual(len(result.operational_events), 0)
