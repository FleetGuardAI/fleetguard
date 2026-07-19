"""
Fleet Intelligence Engine - Tyre Intelligence Config
"""

from pydantic import BaseModel


class TyreIntelligenceConfig(BaseModel):
    """
    Configuration parameters for the Tyre Intelligence domain.
    Abstracts business thresholds to keep domain checks deterministic and pure.
    """
    minimum_tread_depth_mm: float = 2.0
    maximum_pressure_deviation_psi: float = 5.0
    maximum_tyre_age_days: int = 1825  # 5 years
    critical_damage_types: list[str] = ["CRITICAL"]

    model_config = {
        "frozen": True,
        "extra": "forbid"
    }
