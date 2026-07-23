"""
Attachment Processing Framework - Repository
"""

import abc
from typing import Dict, Optional
from infrastructure.attachments.models import Attachment


class AttachmentRepository(abc.ABC):
    """
    Interface for attachment persistence and duplicate detection.
    """

    @abc.abstractmethod
    def save(self, attachment: Attachment) -> None:
        """
        Persists attachment metadata to storage.
        """
        pass

    @abc.abstractmethod
    def exists_by_checksum(self, checksum: str) -> bool:
        """
        Checks if an attachment with the given checksum has already been processed.
        Used for deduplication.
        """
        pass


class InMemoryAttachmentRepository(AttachmentRepository):
    """
    In-memory implementation of the AttachmentRepository.
    Primarily used for testing and duplicate detection prototyping.
    """
    def __init__(self):
        # Maps checksum to Attachment
        self._store: Dict[str, Attachment] = {}

    def save(self, attachment: Attachment) -> None:
        if attachment.checksum:
            self._store[attachment.checksum] = attachment

    def exists_by_checksum(self, checksum: str) -> bool:
        return checksum in self._store

    def clear(self) -> None:
        """
        Clears the repository.
        """
        self._store.clear()
