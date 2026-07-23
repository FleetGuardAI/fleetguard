import unittest
from infrastructure.attachments.models import Attachment
from infrastructure.attachments.routing import determine_processor_route

class TestRouting(unittest.TestCase):
    def test_routing_image(self):
        att = Attachment(
            media_type="image",
            mime_type="image/png",
            storage_uri="s3://bucket/test.png",
            source_channel="whatsapp",
            uploader="+123"
        )
        self.assertEqual(determine_processor_route(att), "ImageProcessor")

    def test_routing_document(self):
        att = Attachment(
            media_type="document",
            mime_type="application/pdf",
            storage_uri="s3://bucket/test.pdf",
            source_channel="whatsapp",
            uploader="+123"
        )
        self.assertEqual(determine_processor_route(att), "DocumentProcessor")

    def test_routing_audio(self):
        att = Attachment(
            media_type="audio",
            mime_type="audio/mpeg",
            storage_uri="s3://bucket/test.mp3",
            source_channel="whatsapp",
            uploader="+123"
        )
        self.assertEqual(determine_processor_route(att), "AudioProcessor")

    def test_routing_video(self):
        att = Attachment(
            media_type="video",
            mime_type="video/mp4",
            storage_uri="s3://bucket/test.mp4",
            source_channel="whatsapp",
            uploader="+123"
        )
        self.assertEqual(determine_processor_route(att), "VideoProcessor")

    def test_routing_unsupported(self):
        att = Attachment(
            media_type="unknown",
            mime_type="application/xml",
            storage_uri="s3://bucket/test.xml",
            source_channel="whatsapp",
            uploader="+123"
        )
        with self.assertRaises(ValueError):
            determine_processor_route(att)
