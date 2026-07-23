"""
Fleet Intelligence Engine - Cross-Domain Models
"""

import uuid
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile


class InsightType(str, Enum):
    """
    Categorization of the cross-domain insight discovered.
    """
    CORRELATION = "CORRELATION"
    DEPENDENCY = "DEPENDENCY"
    OPERATIONAL_PATTERN = "OPERATIONAL_PATTERN"
    COMPLIANCE_PATTERN = "COMPLIANCE_PATTERN"


class InsightStrength(str, Enum):
    """
    Confidence or severity of the discovered cross-domain insight.
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class FleetInsight(BaseModel):
    """
    Immutable representation of an operational insight spanning multiple domains.
    Preserves explainability by retaining references to the contributing DomainRiskProfiles.
    """
    insight_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    insight_key: str
    insight_type: InsightType
    insight_strength: InsightStrength
    summary: str
    supporting_profiles: List[DomainRiskProfile] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }


class FleetInsightCollection(BaseModel):
    """
    A collection of cross-domain insights resulting from an execution run.
    """
    insights: List[FleetInsight] = Field(default_factory=list)
    execution_time: float = 0.0
    analyzer_results: Dict[str, str] = Field(default_factory=dict)
    
    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
