import unittest
from typing import Dict, Any, List
from infrastructure.communication.registry import CommunicationChannelRegistry
from infrastructure.communication.base import BaseCommunicationChannel
from infrastructure.communication.models import Communication, Attachment


class DummyChannelA(BaseCommunicationChannel):
    @classmethod
    def key(cls) -> str:
        return "dummy.a"

    def validate(self, payload: Dict[str, Any]) -> bool:
        return True

    def extract_attachments(self, payload: Dict[str, Any]) -> List[Attachment]:
        return []

    def normalize(self, payload: Dict[str, Any], attachments: List[Attachment]) -> Communication:
        pass


class DummyChannelB(BaseCommunicationChannel):
    @classmethod
    def key(cls) -> str:
        return "dummy.b"

    def validate(self, payload: Dict[str, Any]) -> bool:
        return True

    def extract_attachments(self, payload: Dict[str, Any]) -> List[Attachment]:
        return []

    def normalize(self, payload: Dict[str, Any], attachments: List[Attachment]) -> Communication:
        pass


class TestCommunicationRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = CommunicationChannelRegistry()

    def test_registration_and_lookup(self):
        self.registry.register(DummyChannelA)
        channel = self.registry.get_channel("dummy.a")
        self.assertEqual(channel, DummyChannelA)

    def test_duplicate_registration(self):
        self.registry.register(DummyChannelA)
        with self.assertRaises(ValueError):
            self.registry.register(DummyChannelA)

    def test_missing_lookup(self):
        with self.assertRaises(KeyError):
            self.registry.get_channel("missing")

    def test_deterministic_ordering(self):
        self.registry.register(DummyChannelB)
        self.registry.register(DummyChannelA)
        
        channels = self.registry.get_all_channels()
        self.assertEqual(channels[0], DummyChannelB)
        self.assertEqual(channels[1], DummyChannelA)
