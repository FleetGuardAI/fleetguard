import unittest
from infrastructure.attachments.models import Attachment
from infrastructure.documents.extractors import MockOCRExtractor, MockEmbeddedTextExtractor, select_extraction_strategy

class TestExtractors(unittest.TestCase):
    def test_mock_ocr_extractor(self):
        att = Attachment(
            media_type="image",
            mime_type="image/jpeg",
            storage_uri="s3://bucket/test.jpg",
            source_channel="whatsapp",
            uploader="+123",
            metadata={"mock_text": "TEST OCR CONTENT"}
        )
        extractor = MockOCRExtractor()
        text, diag = extractor.extract(att)
        self.assertEqual(text, "TEST OCR CONTENT")
        self.assertEqual(diag.engine, "MockOCREngine")
        self.assertEqual(diag.detected_language, "en")

    def test_mock_embedded_extractor(self):
        att = Attachment(
            media_type="document",
            mime_type="application/pdf",
            storage_uri="s3://bucket/test.pdf",
            source_channel="whatsapp",
            uploader="+123",
            metadata={"mock_text": "TEST EMBEDDED CONTENT"}
        )
        extractor = MockEmbeddedTextExtractor()
        text, diag = extractor.extract(att)
        self.assertEqual(text, "TEST EMBEDDED CONTENT")
        self.assertEqual(diag.engine, "MockEmbeddedTextEngine")

    def test_select_strategy(self):
        att_img = Attachment(media_type="image", mime_type="image/png", storage_uri="s3", source_channel="test", uploader="test")
        self.assertIsInstance(select_extraction_strategy(att_img), MockOCRExtractor)
        
        att_pdf = Attachment(media_type="document", mime_type="application/pdf", storage_uri="s3", source_channel="test", uploader="test")
        self.assertIsInstance(select_extraction_strategy(att_pdf), MockEmbeddedTextExtractor)
