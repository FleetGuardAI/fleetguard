import unittest
from domain.document_interpretation.interpreters.fuel_receipt import FuelReceiptInterpreter
from domain.document_interpretation.interpreters.unknown import UnknownInterpreter
from infrastructure.documents.models import StructuredDocument, DocumentFamily, ExtractedField
from domain.document_interpretation.events import FuelPurchaseRecorded
from domain.document_interpretation.models import BusinessDocumentType

class TestInterpreters(unittest.TestCase):
    def test_fuel_receipt_supports(self):
        interpreter = FuelReceiptInterpreter()
        doc = StructuredDocument(
            attachment_id="att-1",
            document_family=DocumentFamily.RECEIPT,
            extraction_method="ocr",
            extracted_text="FUEL BILL"
        )
        self.assertTrue(interpreter.supports(doc))
        
        doc_wrong_family = StructuredDocument(
            attachment_id="att-1",
            document_family=DocumentFamily.INVOICE,
            extraction_method="ocr",
            extracted_text="FUEL BILL"
        )
        self.assertFalse(interpreter.supports(doc_wrong_family))

    def test_fuel_receipt_interpret(self):
        interpreter = FuelReceiptInterpreter()
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
        events = interpreter.interpret(doc)
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], FuelPurchaseRecorded)
        self.assertEqual(events[0].total_amount, 100.0)

    def test_unknown_interpreter(self):
        interpreter = UnknownInterpreter()
        doc = StructuredDocument(
            attachment_id="att-1",
            document_family=DocumentFamily.UNKNOWN,
            extraction_method="ocr",
            extracted_text="BLAH BLAH"
        )
        self.assertTrue(interpreter.supports(doc))
        self.assertEqual(len(interpreter.validate(doc)), 0)
        self.assertEqual(len(interpreter.interpret(doc)), 0)
        self.assertEqual(interpreter.get_business_type(), BusinessDocumentType.UNKNOWN)
