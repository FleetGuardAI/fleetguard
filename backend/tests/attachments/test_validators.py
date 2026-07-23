import unittest
from infrastructure.attachments.models import Attachment
from infrastructure.attachments.validators import validate_max_size, validate_mime_type, validate_missing_file_reference

class TestValidators(unittest.TestCase):
    def setUp(self):
        self.att = Attachment(
            media_type="image",
            mime_type="image/jpeg",
            storage_uri="s3://bucket/test.jpg",
            source_channel="whatsapp",
            uploader="+123",
            file_size=1024
        )

    def test_max_size(self):
        self.assertTrue(validate_max_size(self.att, 2048))
        with self.assertRaises(ValueError):
            validate_max_size(self.att, 500)

    def test_mime_type(self):
        self.assertTrue(validate_mime_type(self.att))
        
        att2 = Attachment(
            media_type="unknown",
            mime_type="application/unknown",
            storage_uri="s3://bucket/test.unknown",
            source_channel="whatsapp",
            uploader="+123"
        )
        with self.assertRaises(ValueError):
            validate_mime_type(att2)

    def test_missing_file_reference(self):
        self.assertTrue(validate_missing_file_reference(self.att))
        
        att3 = Attachment(
            media_type="image",
            mime_type="image/jpeg",
            storage_uri="",
            source_channel="whatsapp",
            uploader="+123"
        )
        with self.assertRaises(ValueError):
            validate_missing_file_reference(att3)
