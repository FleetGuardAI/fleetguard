"""
FleetGuard — Evidence Package Schema
"""

import uuid
from typing import List

from pydantic import BaseModel, Field


class EvidencePackage(BaseModel):
    """
    Represents the output of the Evidence Orchestrator for a given Operational Event.
    This schema is serialized and included in the EVIDENCE_PACKAGE_READY event payload.
    """
    event_id: uuid.UUID = Field(
        ...,
        description="The ID of the parent Operational Event."
    )
    
    # Provider Tracking
    expected_providers: List[str] = Field(
        default_factory=list,
        description="Names of providers that were triggered to gather evidence."
    )
    completed_providers: List[str] = Field(
        default_factory=list,
        description="Names of providers that successfully returned evidence."
    )
    failed_providers: List[str] = Field(
        default_factory=list,
        description="Names of providers that encountered an internal error."
    )
    timed_out_providers: List[str] = Field(
        default_factory=list,
        description="Names of providers that failed to complete within the timeout window."
    )
    
    # Evidence Tracking
    collected_evidence: List[uuid.UUID] = Field(
        default_factory=list,
        description="IDs of all successfully created Evidence records."
    )
    
    # Metadata
    collection_status: str = Field(
        ...,
        description="Overall status of the orchestration run (e.g., COMPLETED, PARTIAL, FAILED)."
    )
