import unittest
from infrastructure.documents.parsers.invoice import InvoiceParser
from infrastructure.documents.parsers.unknown import UnknownParser

class TestDocumentParsers(unittest.TestCase):
    def test_invoice_parser(self):
        parser = InvoiceParser()
        fields = parser.parse("TAX INVOICE 100.00")
        self.assertTrue(any(f.name == "invoice_number" for f in fields))
        self.assertTrue(any(f.name == "total_amount" for f in fields))
        
    def test_unknown_parser(self):
        parser = UnknownParser()
        fields = parser.parse("Hello World")
        self.assertEqual(fields[0].name, "raw_text_length")
        self.assertEqual(fields[0].value, 11)
