"""
FleetGuard — Evidence Provider Registry
"""

import logging
from typing import List, Optional

from infrastructure.evidence.provider import BaseEvidenceProvider

logger = logging.getLogger("fleetguard.infrastructure.evidence.registry")


class EvidenceProviderRegistry:
    """
    Maintains a list of registered Evidence Providers.
    Acts purely as a catalog. Contains no orchestration or execution logic.
    """
    def __init__(self) -> None:
        self._providers: List[BaseEvidenceProvider] = []
        self._provider_map: dict[str, BaseEvidenceProvider] = {}

    def register(self, provider: BaseEvidenceProvider) -> None:
        """
        Register a new Evidence Provider.
        """
        if provider.name in self._provider_map:
            raise ValueError(f"Evidence Provider '{provider.name}' is already registered.")
        
        self._providers.append(provider)
        self._provider_map[provider.name] = provider
        logger.info(f"Registered Evidence Provider: {provider.name}")

    def get(self, name: str) -> Optional[BaseEvidenceProvider]:
        """
        Retrieve a provider by name.
        """
        return self._provider_map.get(name)

    def list(self) -> List[BaseEvidenceProvider]:
        """
        List all registered providers.
        """
        return list(self._providers)
