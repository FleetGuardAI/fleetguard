"""
Fleet Intelligence Engine - Check Models
"""

from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class CheckStatus(str, Enum):
    """
    Status of an executed Intelligence Check.
    Checks evaluate facts objectively; they do not calculate business risk.
    """
    PASS = "PASS"
    FAIL = "FAIL"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class CheckResult(BaseModel):
    """
    Immutable result of a check execution.
    Retains full explainability fields to allow recommendations to trace 
    decisions back to the originating checks.
    """
    check_key: str
    check_name: str
    status: CheckStatus
    message: str
    evidence_used: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float = 0.0

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
