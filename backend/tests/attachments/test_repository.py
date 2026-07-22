import unittest
from infrastructure.attachments.models import Attachment
from infrastructure.attachments.repository import InMemoryAttachmentRepository

class TestAttachmentRepository(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryAttachmentRepository()

    def test_save_and_exists(self):
        att = Attachment(
            media_type="image",
            mime_type="image/jpeg",
            storage_uri="s3://bucket/test.jpg",
            source_channel="whatsapp",
            uploader="+123",
            checksum="mychecksum123"
        )
        
        self.assertFalse(self.repo.exists_by_checksum("mychecksum123"))
        
        self.repo.save(att)
        
        self.assertTrue(self.repo.exists_by_checksum("mychecksum123"))
        self.assertFalse(self.repo.exists_by_checksum("other"))
        
    def test_clear(self):
        att = Attachment(
            media_type="image",
            mime_type="image/jpeg",
            storage_uri="s3://bucket/test.jpg",
            source_channel="whatsapp",
            uploader="+123",
            checksum="mychecksum123"
        )
        self.repo.save(att)
        self.assertTrue(self.repo.exists_by_checksum("mychecksum123"))
        
        self.repo.clear()
        self.assertFalse(self.repo.exists_by_checksum("mychecksum123"))
