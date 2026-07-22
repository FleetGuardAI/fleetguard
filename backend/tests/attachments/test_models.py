import unittest
from datetime import datetime, timezone
from pydantic import ValidationError
from infrastructure.attachments.models import Attachment, AttachmentStatus, AttachmentProcessingResult

class TestAttachmentModels(unittest.TestCase):
    def test_attachment_immutability(self):
        att = Attachment(
            filename="test.jpg",
            media_type="image",
            mime_type="image/jpeg",
            file_size=1024,
            checksum="abc",
            storage_uri="s3://bucket/test.jpg",
            uploaded_at=datetime.now(timezone.utc),
            source_channel="whatsapp",
            uploader="+123"
        )
        
        with self.assertRaises(ValidationError):
            att.filename = "new.jpg"
            
        with self.assertRaises(ValidationError):
            att.new_field = "new"

    def test_processing_result_immutability(self):
        att = Attachment(
            media_type="image",
            mime_type="image/jpeg",
            storage_uri="s3://bucket/test.jpg",
            source_channel="whatsapp",
            uploader="+123"
        )
        res = AttachmentProcessingResult(
            attachment=att,
            processing_status=AttachmentStatus.ROUTED,
            execution_time=0.1
        )
        
        with self.assertRaises(ValidationError):
            res.execution_time = 0.5
