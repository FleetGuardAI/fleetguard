"""
FleetGuard — Evidence Provider SDK Schemas
Provides the standard data contracts for Evidence Providers.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from schemas.operational_event import OperationalEventResponse
from models.evidence import EvidenceType


class ProviderStatus(str):
    """Constants for provider execution status."""
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"


class EvidenceRequest(BaseModel):
    """
    Standardized input passed to every Evidence Provider.
    Encapsulates the event and any operational context.
    """
    event: OperationalEventResponse
    context: Dict[str, Any] = Field(default_factory=dict)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class EvidenceResult(BaseModel):
    """
    Standardized output from an Evidence Provider.
    Contains raw evidence data instead of a database ID, ensuring providers
    remain stateless and persistence-agnostic.
    """
    provider_name: str
    status: str
    evidence_type: EvidenceType
    
    # The actual raw evidence payload collected by the provider
    raw_data: Optional[Dict[str, Any]] = None
    summary: str = ""
    details: Optional[str] = None
    
    confidence: float = 1.0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    execution_time_ms: float = 0.0
