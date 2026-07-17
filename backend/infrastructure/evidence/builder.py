"""
FleetGuard — Evidence Package Builder
"""

import uuid
from typing import List

from schemas.evidence_sdk import EvidenceResult, ProviderStatus
from schemas.evidence_package import EvidencePackage


class EvidencePackageBuilder:
    """
    Stateful builder for creating an EvidencePackage from provider results.
    """
    def __init__(self, event_id: uuid.UUID) -> None:
        self.event_id = event_id
        self.expected_providers: List[str] = []
        self.completed_providers: List[str] = []
        self.failed_providers: List[str] = []
        self.timed_out_providers: List[str] = []
        self.collected_evidence: List[uuid.UUID] = []

    def expect_provider(self, provider_name: str) -> None:
        """Record that a provider is expected to run."""
        self.expected_providers.append(provider_name)

    def record_result(self, result: EvidenceResult, evidence_id: uuid.UUID = None) -> None:
        """Record the outcome of a provider's execution and the persisted evidence_id."""
        if result.status == ProviderStatus.COMPLETED:
            self.completed_providers.append(result.provider_name)
            if evidence_id:
                self.collected_evidence.append(evidence_id)
        elif result.status == ProviderStatus.TIMED_OUT:
            self.timed_out_providers.append(result.provider_name)
        else:
            self.failed_providers.append(result.provider_name)

    def build(self) -> EvidencePackage:
        """
        Construct and return the finalized EvidencePackage.
        Calculates the overall collection_status based on provider outcomes.
        """
        status = "COMPLETED"
        if not self.expected_providers:
            status = "COMPLETED"
        elif self.failed_providers or self.timed_out_providers:
            if self.completed_providers:
                status = "PARTIAL"
            else:
                status = "FAILED"

        return EvidencePackage(
            event_id=self.event_id,
            expected_providers=self.expected_providers,
            completed_providers=self.completed_providers,
            failed_providers=self.failed_providers,
            timed_out_providers=self.timed_out_providers,
            collected_evidence=self.collected_evidence,
            collection_status=status
        )
