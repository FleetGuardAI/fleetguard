import unittest
from infrastructure.attachments.models import Attachment, AttachmentStatus
from infrastructure.attachments.registry import AttachmentHandlerRegistry
from infrastructure.attachments.repository import InMemoryAttachmentRepository
from infrastructure.attachments.executor import AttachmentProcessingExecutor
from infrastructure.attachments.base import BaseAttachmentHandler

class SuccessHandler(BaseAttachmentHandler):
    @classmethod
    def key(cls) -> str: return "test.success"
    def validate(self, attachment: Attachment) -> bool: return True
    def determine_media_type(self, attachment: Attachment) -> str: return "image"
    def route(self, attachment: Attachment) -> str: return "ImageProcessor"

class FailValidationHandler(BaseAttachmentHandler):
    @classmethod
    def key(cls) -> str: return "test.fail"
    def validate(self, attachment: Attachment) -> bool: raise ValueError("Simulated validation failure")
    def determine_media_type(self, attachment: Attachment) -> str: return "image"
    def route(self, attachment: Attachment) -> str: return "ImageProcessor"

class TestAttachmentExecutor(unittest.TestCase):
    def setUp(self):
        self.registry = AttachmentHandlerRegistry()
        self.registry.register(SuccessHandler)
        self.registry.register(FailValidationHandler)
        self.repo = InMemoryAttachmentRepository()
        self.executor = AttachmentProcessingExecutor(self.registry, self.repo)

    def test_executor_success(self):
        att = Attachment(
            media_type="image",
            mime_type="image/jpeg",
            storage_uri="s3://bucket/test.jpg",
            source_channel="whatsapp",
            uploader="+123",
            checksum="abc"
        )
        result = self.executor.process_attachment("test.success", att)
        self.assertEqual(result.processing_status, AttachmentStatus.ROUTED)
        self.assertEqual(result.routed_processor, "ImageProcessor")
        self.assertTrue(self.repo.exists_by_checksum("abc"))

    def test_executor_validation_error(self):
        att = Attachment(
            media_type="image",
            mime_type="image/jpeg",
            storage_uri="s3://bucket/test.jpg",
            source_channel="whatsapp",
            uploader="+123"
        )
        result = self.executor.process_attachment("test.fail", att)
        self.assertEqual(result.processing_status, AttachmentStatus.FAILED)
        self.assertIn("Simulated validation failure", result.error_message)

    def test_executor_missing_handler(self):
        att = Attachment(
            media_type="image",
            mime_type="image/jpeg",
            storage_uri="s3://bucket/test.jpg",
            source_channel="whatsapp",
            uploader="+123"
        )
        result = self.executor.process_attachment("missing", att)
        self.assertEqual(result.processing_status, AttachmentStatus.FAILED)
        
    def test_executor_duplicate(self):
        att1 = Attachment(
            media_type="image",
            mime_type="image/jpeg",
            storage_uri="s3://bucket/test.jpg",
            source_channel="whatsapp",
            uploader="+123",
            checksum="dupe_checksum"
        )
        att2 = Attachment(
            media_type="image",
            mime_type="image/jpeg",
            storage_uri="s3://bucket/other.jpg",
            source_channel="whatsapp",
            uploader="+456",
            checksum="dupe_checksum"
        )
        
        # First process
        result1 = self.executor.process_attachment("test.success", att1)
        self.assertEqual(result1.processing_status, AttachmentStatus.ROUTED)
        
        # Second process with same checksum
        result2 = self.executor.process_attachment("test.success", att2)
        self.assertEqual(result2.processing_status, AttachmentStatus.DUPLICATE)
