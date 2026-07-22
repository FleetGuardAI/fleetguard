"""
Message Gateway Framework - Registry
"""

from typing import Dict, List, Type
import logging
from infrastructure.communication.base import BaseCommunicationChannel


logger = logging.getLogger(__name__)


class CommunicationChannelRegistry:
    """
    Registry for Communication Channels.
    Provides deterministic discovery and execution ordering.
    """
    def __init__(self):
        self._channels: Dict[str, Type[BaseCommunicationChannel]] = {}
        # List preserves deterministic registration ordering
        self._ordered_keys: List[str] = []

    def register(self, channel_class: Type[BaseCommunicationChannel]) -> None:
        """
        Registers a communication channel.
        Raises ValueError if a channel with the same key is already registered.
        """
        key = channel_class.key()
        if key in self._channels:
            raise ValueError(f"Communication Channel with key '{key}' is already registered.")
            
        self._channels[key] = channel_class
        self._ordered_keys.append(key)
        logger.debug(f"Registered Communication Channel: {key} ({channel_class.name()})")

    def get_channel(self, key: str) -> Type[BaseCommunicationChannel]:
        """
        Retrieves a registered channel by key.
        Raises KeyError if the channel is not found.
        """
        if key not in self._channels:
            raise KeyError(f"No Communication Channel found with key '{key}'.")
        return self._channels[key]

    def get_all_channels(self) -> List[Type[BaseCommunicationChannel]]:
        """
        Returns all registered channels in a deterministic order.
        """
        return [self._channels[key] for key in self._ordered_keys]

    def clear(self) -> None:
        """
        Clears all registered channels (mostly useful for testing).
        """
        self._channels.clear()
        self._ordered_keys.clear()
