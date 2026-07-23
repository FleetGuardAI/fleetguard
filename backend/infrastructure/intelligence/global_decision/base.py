"""
Fleet Intelligence Engine - Base Decision Engine
"""

import abc
from typing import List
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile
from infrastructure.intelligence.global_decision.models import Recommendation


class BaseDecisionEngine(abc.ABC):
    """
    Abstract Base Class for all Global Decision Engines.
    
    Decision Engines consume DomainRiskProfiles to generate the final business recommendation.
    They must never access databases, external services, or execute assessments/checks directly.
    """
    
    @classmethod
    @abc.abstractmethod
    def key(cls) -> str:
        """
        Returns the stable unique identifier of the decision engine (e.g., 'global.default_policy').
        """
        pass

    @classmethod
    def name(cls) -> str:
        """
        Returns the unique human-readable name of the decision engine. By default, the class name.
        """
        return cls.__name__

    @classmethod
    def version(cls) -> str:
        """
        Returns the version of this decision logic.
        """
        return "1.0"

    @abc.abstractmethod
    def execute(self, profiles: List[DomainRiskProfile]) -> Recommendation:
        """
        Executes the global decision logic against the provided DomainRiskProfiles.
        
        Must return a Recommendation.
        Given identical risk profiles, this method must always produce the same result.
        
        The implementation is responsible for filtering the provided profiles 
        to find what it needs, determining the execution status (COMPLETE/PARTIAL/INCONCLUSIVE), 
        and outputting the final RecommendationStatus.
        """
        pass
