import unittest
from domain.document_interpretation.registry import DocumentInterpreterRegistry
from domain.document_interpretation.interpreters.fuel_receipt import FuelReceiptInterpreter
from domain.document_interpretation.interpreters.tyre_invoice import TyreInvoiceInterpreter
from infrastructure.documents.models import StructuredDocument, DocumentFamily

class TestInterpreterRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = DocumentInterpreterRegistry()
        self.registry.register(FuelReceiptInterpreter)
        self.registry.register(TyreInvoiceInterpreter)

    def test_find_fuel_receipt(self):
        doc = StructuredDocument(
            attachment_id="att-1",
            document_family=DocumentFamily.RECEIPT,
            extraction_method="ocr",
            extracted_text="FUEL RECEIPT"
        )
        interpreter = self.registry.find_interpreter(doc)
        self.assertIsInstance(interpreter, FuelReceiptInterpreter)

    def test_find_tyre_invoice(self):
        doc = StructuredDocument(
            attachment_id="att-1",
            document_family=DocumentFamily.INVOICE,
            extraction_method="ocr",
            extracted_text="TYRE REPLACEMENT INVOICE"
        )
        interpreter = self.registry.find_interpreter(doc)
        self.assertIsInstance(interpreter, TyreInvoiceInterpreter)

    def test_not_found(self):
        doc = StructuredDocument(
            attachment_id="att-1",
            document_family=DocumentFamily.CERTIFICATE,
            extraction_method="ocr",
            extracted_text="UNKNOWN TEXT"
        )
        interpreter = self.registry.find_interpreter(doc)
        self.assertIsNone(interpreter)
        
    def test_duplicate_registration(self):
        with self.assertRaises(ValueError):
            self.registry.register(FuelReceiptInterpreter)
