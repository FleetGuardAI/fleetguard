"""
FleetGuard — Validation Result Schema
"""

import enum
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field
from schemas.validation_sdk import RuleResult


class ValidationVerdict(str, enum.Enum):
    """
    The outcome of the Validation Engine evaluating an Evidence Package.
    """
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"


class ValidationResult(BaseModel):
    """
    The final output of the Validation Engine.
    Serialized and attached to the VALIDATION_SUCCEEDED/FAILED/DISPUTED event payload.
    """
    verdict: ValidationVerdict = Field(..., description="The final trust decision")
    validation_score: Optional[float] = Field(
        None, 
        description="Optional overall validation score. Not the primary decision mechanism, purely metadata."
    )
    passed_rules: List[str] = Field(default_factory=list, description="Names of rules that passed")
    failed_rules: List[RuleResult] = Field(
        default_factory=list, 
        description="Details of rules that failed"
    )
    warnings: List[RuleResult] = Field(default_factory=list, description="Non-blocking observations (INFO/WARNING severity failures)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Aggregated validation metadata")
