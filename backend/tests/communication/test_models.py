import unittest
from datetime import datetime, timezone
from pydantic import ValidationError
from infrastructure.communication.models import Communication, Attachment, CommunicationType, CommunicationProcessingResult, CommunicationProcessingStatus


class TestCommunicationModels(unittest.TestCase):
    def test_communication_immutability(self):
        comm = Communication(
            message_id="123",
            channel="test",
            sender="+123",
            receiver="+456",
            timestamp=datetime.now(timezone.utc),
            message_type=CommunicationType.TEXT,
            text="Hello"
        )
        
        with self.assertRaises(ValidationError):
            comm.text = "Changed"
            
        with self.assertRaises(ValidationError):
            comm.new_field = "new"

    def test_attachment_immutability(self):
        att = Attachment(
            media_type="image/jpeg",
            storage_uri="s3://bucket/image.jpg",
            filename="image.jpg",
            file_size=1024,
            checksum="abc"
        )
        
        with self.assertRaises(ValidationError):
            att.filename = "new.jpg"
            
    def test_processing_result_immutability(self):
        res = CommunicationProcessingResult(
            processing_status=CommunicationProcessingStatus.SUCCESS,
            execution_time=0.1
        )
        
        with self.assertRaises(ValidationError):
            res.execution_time = 0.5
