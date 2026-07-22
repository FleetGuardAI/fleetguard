import unittest
from infrastructure.attachments.registry import AttachmentHandlerRegistry
from infrastructure.attachments.base import BaseAttachmentHandler
from infrastructure.attachments.models import Attachment

class DummyHandlerA(BaseAttachmentHandler):
    @classmethod
    def key(cls) -> str:
        return "dummy.a"
    def validate(self, attachment: Attachment) -> bool:
        return True
    def determine_media_type(self, attachment: Attachment) -> str:
        return "dummy"
    def route(self, attachment: Attachment) -> str:
        return "DummyProcessor"

class DummyHandlerB(BaseAttachmentHandler):
    @classmethod
    def key(cls) -> str:
        return "dummy.b"
    def validate(self, attachment: Attachment) -> bool:
        return True
    def determine_media_type(self, attachment: Attachment) -> str:
        return "dummy"
    def route(self, attachment: Attachment) -> str:
        return "DummyProcessor"

class TestAttachmentRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = AttachmentHandlerRegistry()

    def test_registration_and_lookup(self):
        self.registry.register(DummyHandlerA)
        handler = self.registry.get_handler("dummy.a")
        self.assertEqual(handler, DummyHandlerA)

    def test_duplicate_registration(self):
        self.registry.register(DummyHandlerA)
        with self.assertRaises(ValueError):
            self.registry.register(DummyHandlerA)

    def test_missing_lookup(self):
        with self.assertRaises(KeyError):
            self.registry.get_handler("missing")

    def test_deterministic_ordering(self):
        self.registry.register(DummyHandlerB)
        self.registry.register(DummyHandlerA)
        
        handlers = self.registry.get_all_handlers()
        self.assertEqual(handlers[0], DummyHandlerB)
        self.assertEqual(handlers[1], DummyHandlerA)
