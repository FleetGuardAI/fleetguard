import unittest
from infrastructure.attachments.models import Attachment
from infrastructure.documents.registry import DocumentParserRegistry
from infrastructure.documents.executor import DocumentProcessingExecutor
from infrastructure.documents.models import DocumentProcessingStatus

class TestDocumentExecutor(unittest.TestCase):
    def setUp(self):
        self.registry = DocumentParserRegistry()
        self.executor = DocumentProcessingExecutor(self.registry)

    def test_missing_parser_classification(self):
        # We haven't registered any parsers in this test.
        # It should classify as INVOICE but fail to find a parser.
        att = Attachment(
            media_type="image",
            mime_type="image/jpeg",
            storage_uri="s3://bucket/test.jpg",
            source_channel="whatsapp",
            uploader="+123",
            metadata={"mock_text": "THIS IS AN INVOICE"}
        )
        
        result = self.executor.process_attachment(att)
        self.assertEqual(result.processing_status, DocumentProcessingStatus.UNKNOWN_TYPE)
        self.assertIn("No parser available for document family INVOICE", result.error_message)
