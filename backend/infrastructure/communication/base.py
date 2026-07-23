"""
Message Gateway Framework - Base Channel
"""

import abc
from typing import Dict, Any, List
from infrastructure.communication.models import Communication, Attachment


class BaseCommunicationChannel(abc.ABC):
    """
    Abstract Base Class for all Communication Channels (e.g. WhatsApp, Email).
    Provides the contract for validating, normalizing, and extracting inbound messages.
    """
    
    @classmethod
    @abc.abstractmethod
    def key(cls) -> str:
        """
        Returns the unique identifier of the channel (e.g., 'whatsapp').
        """
        pass

    @classmethod
    def name(cls) -> str:
        """
        Returns the human-readable name of the channel. By default, the class name.
        """
        return cls.__name__

    @classmethod
    def version(cls) -> str:
        """
        Returns the version of this channel adapter logic.
        """
        return "1.0.0"

    @abc.abstractmethod
    def validate(self, payload: Dict[str, Any]) -> bool:
        """
        Validates the incoming raw webhook payload.
        Should raise ValueError or return False if invalid.
        """
        pass

    @abc.abstractmethod
    def extract_attachments(self, payload: Dict[str, Any]) -> List[Attachment]:
        """
        Extracts attachment metadata (storage URIs, checksums, media_types) from the payload.
        Does NOT parse the content of the attachments.
        """
        pass

    @abc.abstractmethod
    def normalize(self, payload: Dict[str, Any], attachments: List[Attachment]) -> Communication:
        """
        Normalizes the raw payload and extracted attachments into an immutable Communication model.
        """
        pass

    def receive(self, payload: Dict[str, Any]) -> Communication:
        """
        The primary execution flow for a single channel.
        Validates, extracts attachments, and normalizes into a Communication model.
        """
        self.validate(payload)
        attachments = self.extract_attachments(payload)
        return self.normalize(payload, attachments)
