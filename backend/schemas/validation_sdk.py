"""
FleetGuard — Validation Rule SDK Schemas
Provides standard data contracts for the Validation Rule Engine.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from schemas.operational_event import OperationalEventResponse
from schemas.evidence_package import EvidencePackage


class RuleSeverity(str, Enum):
    """Severity level of a rule failure."""
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class RuleCategory(str, Enum):
    """Categorization of validation rules."""
    STRUCTURAL = "STRUCTURAL"
    BUSINESS_LOGIC = "BUSINESS_LOGIC"
    COMPLIANCE = "COMPLIANCE"
    FRAUD = "FRAUD"
    OTHER = "OTHER"


class ValidationContext(BaseModel):
    """
    Standardized input passed to every Validation Rule.
    Contains all context required to evaluate the rule without querying databases.
    """
    event: OperationalEventResponse
    evidence_package: EvidencePackage
    # Pre-loaded evidence records (e.g. from EvidenceService)
    evidence_records: List[Dict[str, Any]] = Field(default_factory=list)
    # Business state pre-loaded by the Orchestrator/Consumer
    business_state: Dict[str, Any] = Field(default_factory=dict)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RuleResult(BaseModel):
    """
    Standardized output from a Validation Rule.
    """
    rule_name: str
    passed: bool
    severity: RuleSeverity
    confidence: float = 1.0
    message: str
    recommendation: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
