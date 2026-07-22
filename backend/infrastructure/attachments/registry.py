"""
Attachment Processing Framework - Registry
"""

from typing import Dict, List, Type
import logging
from infrastructure.attachments.base import BaseAttachmentHandler


logger = logging.getLogger(__name__)


class AttachmentHandlerRegistry:
    """
    Registry for Attachment Handlers.
    Provides deterministic discovery and execution ordering.
    """
    def __init__(self):
        self._handlers: Dict[str, Type[BaseAttachmentHandler]] = {}
        self._ordered_keys: List[str] = []

    def register(self, handler_class: Type[BaseAttachmentHandler]) -> None:
        """
        Registers an attachment handler.
        Raises ValueError if a handler with the same key is already registered.
        """
        key = handler_class.key()
        if key in self._handlers:
            raise ValueError(f"Attachment Handler with key '{key}' is already registered.")
            
        self._handlers[key] = handler_class
        self._ordered_keys.append(key)
        logger.debug(f"Registered Attachment Handler: {key} ({handler_class.name()})")

    def get_handler(self, key: str) -> Type[BaseAttachmentHandler]:
        """
        Retrieves a registered handler by key.
        Raises KeyError if the handler is not found.
        """
        if key not in self._handlers:
            raise KeyError(f"No Attachment Handler found with key '{key}'.")
        return self._handlers[key]

    def get_all_handlers(self) -> List[Type[BaseAttachmentHandler]]:
        """
        Returns all registered handlers in a deterministic order.
        """
        return [self._handlers[key] for key in self._ordered_keys]

    def clear(self) -> None:
        """
        Clears all registered handlers.
        """
        self._handlers.clear()
        self._ordered_keys.clear()
