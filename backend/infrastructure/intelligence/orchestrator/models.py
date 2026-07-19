"""
Fleet Intelligence Engine - Orchestrator Models
"""

import uuid
from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.models import CheckResult
from infrastructure.intelligence.assessments.models import AssessmentResult
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile
from infrastructure.intelligence.global_decision.models import Recommendation


class IntelligenceExecutionStatus(str, Enum):
    """Status of the overall pipeline execution."""
    COMPLETE = "COMPLETE"
    ERROR = "ERROR"


class ExecutionTrace(BaseModel):
    """
    Detailed internal trace capturing all intermediate outputs.
    Allows for future debugging and explainability tools to trace the entire pipeline.
    """
    evidence_package: EvidencePackage
    check_results: List[CheckResult] = Field(default_factory=list)
    assessment_results: List[AssessmentResult] = Field(default_factory=list)
    domain_risk_profiles: List[DomainRiskProfile] = Field(default_factory=list)

    model_config = {
        "arbitrary_types_allowed": True,
        "frozen": True,
        "extra": "forbid"
    }


class IntelligenceExecutionResult(BaseModel):
    """
    Immutable root object containing the results of an end-to-end pipeline execution.
    """
    execution_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    status: IntelligenceExecutionStatus
    recommendations: List[Recommendation] = Field(default_factory=list)
    trace: ExecutionTrace
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float = 0.0

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
