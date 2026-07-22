import unittest
from infrastructure.communication.registry import CommunicationChannelRegistry
from infrastructure.communication.executor import CommunicationGatewayExecutor
from infrastructure.communication.channels.whatsapp import WhatsAppChannel
from infrastructure.communication.models import CommunicationProcessingStatus, CommunicationType


class TestCommunicationPipeline(unittest.TestCase):
    def setUp(self):
        self.registry = CommunicationChannelRegistry()
        self.registry.register(WhatsAppChannel)
        self.executor = CommunicationGatewayExecutor(self.registry)

    def test_whatsapp_text_pipeline(self):
        payload = {
            "message_id": "msg1",
            "from": "123-456",
            "to": "987-654",
            "timestamp": "2026-07-20T00:36:44Z",
            "type": "text",
            "text": {"body": "Hello world"}
        }
        
        result = self.executor.process_webhook("whatsapp", payload)
        
        self.assertEqual(result.processing_status, CommunicationProcessingStatus.SUCCESS)
        self.assertIsNotNone(result.message)
        
        msg = result.message
        self.assertEqual(msg.message_id, "msg1")
        self.assertEqual(msg.channel, "whatsapp")
        self.assertEqual(msg.sender, "+123456")
        self.assertEqual(msg.receiver, "+987654")
        self.assertEqual(msg.message_type, CommunicationType.TEXT)
        self.assertEqual(msg.text, "Hello world")
        self.assertEqual(len(msg.attachments), 0)

    def test_whatsapp_image_pipeline(self):
        payload = {
            "message_id": "msg2",
            "from": "123",
            "to": "456",
            "timestamp": "2026-07-20T00:36:44Z",
            "type": "image",
            "image": {
                "id": "img1",
                "mime_type": "image/jpeg",
                "link": "https://whatsapp.com/media/img1",
                "sha256": "abc",
                "file_size": 1024,
                "caption": "Look at this"
            }
        }
        
        result = self.executor.process_webhook("whatsapp", payload)
        
        self.assertEqual(result.processing_status, CommunicationProcessingStatus.SUCCESS)
        msg = result.message
        self.assertEqual(msg.message_type, CommunicationType.IMAGE)
        self.assertEqual(msg.text, "Look at this")
        
        self.assertEqual(len(msg.attachments), 1)
        att = msg.attachments[0]
        self.assertEqual(att.media_type, "image/jpeg")
        self.assertEqual(att.storage_uri, "https://whatsapp.com/media/img1")
        self.assertEqual(att.checksum, "abc")
        self.assertEqual(att.file_size, 1024)
