"""
Fleet Intelligence Engine - Assessment Models
"""

import uuid
from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from infrastructure.intelligence.checks.models import CheckResult


class AssessmentStatus(str, Enum):
    """
    Status of an executed Intelligence Assessment.
    Assessments evaluate CheckResults; they do not calculate business risk.
    """
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INCONCLUSIVE = "INCONCLUSIVE"
    ERROR = "ERROR"


class Finding(BaseModel):
    """
    Strongly typed domain finding produced by an Assessment.
    Avoids using generic strings for structured data.
    """
    finding_key: str
    category: str
    summary: str
    details: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class AssessmentResult(BaseModel):
    """
    Immutable result of an assessment execution.
    Retains full explainability fields to allow risk engines to trace 
    decisions back to the originating checks.
    """
    assessment_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    assessment_key: str
    assessment_name: str
    assessment_version: str
    status: AssessmentStatus
    summary: str
    findings: List[Finding] = Field(default_factory=list)
    contributing_checks: List[CheckResult] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float = 0.0

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
