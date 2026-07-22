import unittest
from infrastructure.documents.registry import DocumentParserRegistry
from infrastructure.documents.parsers.invoice import InvoiceParser
from infrastructure.documents.parsers.receipt import ReceiptParser
from infrastructure.documents.models import DocumentFamily

class TestDocumentRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = DocumentParserRegistry()

    def test_registration_and_lookup(self):
        self.registry.register(InvoiceParser)
        parser = self.registry.get_parser_by_family(DocumentFamily.INVOICE)
        self.assertEqual(parser, InvoiceParser)

    def test_duplicate_key_registration(self):
        self.registry.register(InvoiceParser)
        with self.assertRaises(ValueError):
            self.registry.register(InvoiceParser)
            
    def test_missing_lookup(self):
        with self.assertRaises(KeyError):
            self.registry.get_parser_by_family(DocumentFamily.RECEIPT)
