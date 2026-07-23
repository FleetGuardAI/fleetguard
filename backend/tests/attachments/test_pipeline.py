import unittest
from infrastructure.attachments.models import Attachment, AttachmentStatus
from infrastructure.attachments.registry import AttachmentHandlerRegistry
from infrastructure.attachments.repository import InMemoryAttachmentRepository
from infrastructure.attachments.executor import AttachmentProcessingExecutor
from infrastructure.attachments.base import BaseAttachmentHandler
from infrastructure.attachments.validators import validate_max_size, validate_mime_type
from infrastructure.attachments.routing import determine_processor_route

class PDFDocumentHandler(BaseAttachmentHandler):
    @classmethod
    def key(cls) -> str:
        return "pdf_handler"
        
    def validate(self, attachment: Attachment) -> bool:
        validate_max_size(attachment)
        validate_mime_type(attachment, ["application/pdf"])
        return True
        
    def determine_media_type(self, attachment: Attachment) -> str:
        return "document"
        
    def route(self, attachment: Attachment) -> str:
        return determine_processor_route(attachment)


class TestAttachmentPipeline(unittest.TestCase):
    def setUp(self):
        self.registry = AttachmentHandlerRegistry()
        self.registry.register(PDFDocumentHandler)
        self.repo = InMemoryAttachmentRepository()
        self.executor = AttachmentProcessingExecutor(self.registry, self.repo)

    def test_end_to_end_success_and_duplicate(self):
        att = Attachment(
            media_type="document",
            mime_type="application/pdf",
            storage_uri="s3://bucket/invoice.pdf",
            source_channel="whatsapp",
            uploader="+123",
            file_size=1024,
            checksum="pdf123"
        )
        
        # 1. Process for the first time
        result1 = self.executor.process_attachment("pdf_handler", att)
        self.assertEqual(result1.processing_status, AttachmentStatus.ROUTED)
        self.assertEqual(result1.routed_processor, "DocumentProcessor")
        self.assertTrue(self.repo.exists_by_checksum("pdf123"))
        
        # 2. Process duplicate
        att_dupe = Attachment(
            media_type="document",
            mime_type="application/pdf",
            storage_uri="s3://bucket/invoice_copy.pdf",
            source_channel="email",
            uploader="test@test.com",
            file_size=1024,
            checksum="pdf123"
        )
        result2 = self.executor.process_attachment("pdf_handler", att_dupe)
        self.assertEqual(result2.processing_status, AttachmentStatus.DUPLICATE)

    def test_pipeline_validation_failure(self):
        att = Attachment(
            media_type="document",
            mime_type="image/jpeg", # Invalid for this handler
            storage_uri="s3://bucket/invoice.jpg",
            source_channel="whatsapp",
            uploader="+123",
            file_size=1024,
            checksum="jpg123"
        )
        
        result = self.executor.process_attachment("pdf_handler", att)
        self.assertEqual(result.processing_status, AttachmentStatus.FAILED)
        self.assertIn("MIME type 'image/jpeg' is not supported", result.error_message)
        self.assertFalse(self.repo.exists_by_checksum("jpg123"))
