"""
FleetGuard — Evidence Provider Interface
Defines the standard plugin contract for all Evidence Providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from schemas.evidence_sdk import EvidenceRequest, EvidenceResult


class BaseEvidenceProvider(ABC):
    """
    Abstract Base Class for all Evidence Providers.
    Providers act as pure adapters, fetching evidence from external systems.
    They do NOT interact with databases or orchestrators directly.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """A unique string identifier for this provider."""
        pass

    async def initialize(self) -> None:
        """Lifecycle hook: Called once during application startup."""
        pass

    async def health(self) -> bool:
        """Lifecycle hook: Called to check if the provider's external dependencies are healthy."""
        return True

    async def validate_configuration(self, config: Dict[str, Any]) -> bool:
        """Lifecycle hook: Validate dynamic configuration for this provider."""
        return True

    @abstractmethod
    async def applies_to(self, request: EvidenceRequest) -> bool:
        """
        Determine if this provider is applicable to the given EvidenceRequest.
        Must be fast/synchronous to not block the orchestration loop.
        """
        pass

    @abstractmethod
    async def collect(self, request: EvidenceRequest) -> EvidenceResult:
        """
        Execute the evidence gathering process.
        Returns raw evidence data encapsulated in an EvidenceResult.
        """
        pass

    async def shutdown(self) -> None:
        """Lifecycle hook: Called during application shutdown to release resources."""
        pass

