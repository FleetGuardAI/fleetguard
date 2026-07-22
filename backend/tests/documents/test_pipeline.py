import unittest
from infrastructure.attachments.models import Attachment
from infrastructure.documents.registry import DocumentParserRegistry
from infrastructure.documents.executor import DocumentProcessingExecutor
from infrastructure.documents.parsers.invoice import InvoiceParser
from infrastructure.documents.parsers.unknown import UnknownParser
from infrastructure.documents.models import DocumentProcessingStatus, DocumentFamily

class TestDocumentPipeline(unittest.TestCase):
    def setUp(self):
        self.registry = DocumentParserRegistry()
        self.registry.register(InvoiceParser)
        self.registry.register(UnknownParser)
        self.executor = DocumentProcessingExecutor(self.registry)

    def test_end_to_end_invoice_pipeline(self):
        att = Attachment(
            media_type="image",
            mime_type="image/jpeg",
            storage_uri="s3://bucket/invoice.jpg",
            source_channel="whatsapp",
            uploader="+123",
            metadata={"mock_text": "THIS IS A TAX INVOICE"}
        )
        
        result = self.executor.process_attachment(att)
        self.assertEqual(result.processing_status, DocumentProcessingStatus.SUCCESS)
        
        doc = result.structured_document
        self.assertIsNotNone(doc)
        self.assertEqual(doc.document_family, DocumentFamily.INVOICE)
        self.assertEqual(doc.extraction_method, "MockOCREngine")
        self.assertEqual(doc.extracted_text, "THIS IS A TAX INVOICE")
        
        # Verify diagnostics
        self.assertIsNotNone(doc.diagnostics)
        self.assertEqual(doc.diagnostics.detected_language, "en")
        
        # Verify extracted fields
        self.assertTrue(any(f.name == "total_amount" for f in doc.structured_fields))

    def test_end_to_end_unknown_pipeline(self):
        att = Attachment(
            media_type="document",
            mime_type="application/pdf",
            storage_uri="s3://bucket/random.pdf",
            source_channel="email",
            uploader="test@test.com",
            metadata={"mock_text": "Random gibberish text"}
        )
        
        result = self.executor.process_attachment(att)
        self.assertEqual(result.processing_status, DocumentProcessingStatus.SUCCESS)
        
        doc = result.structured_document
        self.assertEqual(doc.document_family, DocumentFamily.UNKNOWN)
        self.assertEqual(doc.extraction_method, "MockEmbeddedTextEngine")
        self.assertEqual(doc.structured_fields[0].name, "raw_text_length")
