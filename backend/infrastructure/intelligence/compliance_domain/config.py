"""
Fleet Intelligence Engine - Compliance Intelligence Config
"""

from typing import List
from pydantic import BaseModel


class ComplianceIntelligenceConfig(BaseModel):
    """
    Configuration parameters for the Compliance Intelligence domain.
    Abstracts business thresholds to keep domain checks deterministic and pure.
    """
    expiry_warning_days: int = 30
    critical_expiry_days: int = 7
    required_document_categories: List[str] = ["REGISTRATION", "INSURANCE", "FITNESS", "POLLUTION", "PERMIT", "DRIVER_LICENSE"]
    mandatory_permit_types: List[str] = ["NATIONAL", "STATE"]
    required_driver_license_classes: List[str] = ["COMMERCIAL", "HEAVY"]

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
