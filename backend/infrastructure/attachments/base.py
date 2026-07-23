"""
Attachment Processing Framework - Base Handler
"""

import abc
from infrastructure.attachments.models import Attachment


class BaseAttachmentHandler(abc.ABC):
    """
    Abstract Base Class for attachment handlers/processors.
    Defines the lifecycle hooks that specialized media handlers must implement.
    """
    
    @classmethod
    @abc.abstractmethod
    def key(cls) -> str:
        """
        Returns the unique identifier of this handler (e.g., 'image_handler').
        """
        pass

    @classmethod
    def name(cls) -> str:
        """
        Returns the human-readable name of the handler.
        """
        return cls.__name__

    @classmethod
    def version(cls) -> str:
        """
        Returns the version of this handler logic.
        """
        return "1.0.0"

    @abc.abstractmethod
    def validate(self, attachment: Attachment) -> bool:
        """
        Validates the attachment object (e.g. format specifics, size bounds).
        Should raise ValueError if invalid.
        """
        pass

    @abc.abstractmethod
    def determine_media_type(self, attachment: Attachment) -> str:
        """
        Determines and returns the explicit media category of the attachment.
        """
        pass

    @abc.abstractmethod
    def route(self, attachment: Attachment) -> str:
        """
        Determines the routing destination (e.g. topic or queue name) for this attachment.
        """
        pass
