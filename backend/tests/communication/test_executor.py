import unittest
from datetime import datetime, timezone
from typing import Dict, Any, List
from infrastructure.communication.registry import CommunicationChannelRegistry
from infrastructure.communication.executor import CommunicationGatewayExecutor
from infrastructure.communication.base import BaseCommunicationChannel
from infrastructure.communication.models import Communication, Attachment, CommunicationProcessingStatus, CommunicationType


class SuccessChannel(BaseCommunicationChannel):
    @classmethod
    def key(cls) -> str:
        return "test.success"

    def validate(self, payload: Dict[str, Any]) -> bool:
        return True

    def extract_attachments(self, payload: Dict[str, Any]) -> List[Attachment]:
        return []

    def normalize(self, payload: Dict[str, Any], attachments: List[Attachment]) -> Communication:
        return Communication(
            message_id="1",
            channel="test.success",
            sender="+1",
            receiver="+2",
            timestamp=datetime.now(timezone.utc),
            message_type=CommunicationType.TEXT,
            text="Success"
        )


class FailValidationChannel(BaseCommunicationChannel):
    @classmethod
    def key(cls) -> str:
        return "test.fail"

    def validate(self, payload: Dict[str, Any]) -> bool:
        raise ValueError("Simulated validation failure")

    def extract_attachments(self, payload: Dict[str, Any]) -> List[Attachment]:
        return []

    def normalize(self, payload: Dict[str, Any], attachments: List[Attachment]) -> Communication:
        pass


class TestCommunicationExecutor(unittest.TestCase):
    def setUp(self):
        self.registry = CommunicationChannelRegistry()
        self.registry.register(SuccessChannel)
        self.registry.register(FailValidationChannel)
        self.executor = CommunicationGatewayExecutor(self.registry)

    def test_executor_success(self):
        result = self.executor.process_webhook("test.success", {})
        self.assertEqual(result.processing_status, CommunicationProcessingStatus.SUCCESS)
        self.assertIsNotNone(result.message)
        self.assertEqual(result.message.text, "Success")

    def test_executor_validation_error(self):
        result = self.executor.process_webhook("test.fail", {})
        self.assertEqual(result.processing_status, CommunicationProcessingStatus.VALIDATION_ERROR)
        self.assertIsNone(result.message)
        self.assertIn("Simulated validation failure", result.error_message)

    def test_executor_missing_channel(self):
        result = self.executor.process_webhook("missing", {})
        self.assertEqual(result.processing_status, CommunicationProcessingStatus.SYSTEM_ERROR)
        self.assertIsNone(result.message)
