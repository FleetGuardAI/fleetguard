"""
Fleet Intelligence Engine - Base Domain Risk Engine
"""

import abc
from typing import List
from infrastructure.intelligence.assessments.models import AssessmentResult
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile


class BaseDomainRiskEngine(abc.ABC):
    """
    Abstract Base Class for all Domain Risk Engines.
    
    Risk Engines consume AssessmentResults to quantify business risk within a specific domain.
    They must never access databases, external services, or make global recommendations.
    """
    
    @classmethod
    @abc.abstractmethod
    def key(cls) -> str:
        """
        Returns the stable unique identifier of the risk engine (e.g., 'fuel.transaction_risk').
        """
        pass

    @classmethod
    def name(cls) -> str:
        """
        Returns the unique human-readable name of the risk engine. By default, the class name.
        """
        return cls.__name__

    @classmethod
    def version(cls) -> str:
        """
        Returns the version of this risk logic.
        """
        return "1.0"

    @classmethod
    @abc.abstractmethod
    def required_assessments(cls) -> List[str]:
        """
        Declares the stable assessment keys strictly required to quantify risk.
        """
        pass

    @classmethod
    def optional_assessments(cls) -> List[str]:
        """
        Declares the stable assessment keys that the risk engine can optionally use if present.
        """
        return []

    @abc.abstractmethod
    def execute(self, assessments: List[AssessmentResult]) -> DomainRiskProfile:
        """
        Executes the risk quantification logic against the provided AssessmentResults.
        
        Must return a DomainRiskProfile.
        Given identical assessments, this method must always produce the same result.
        
        The implementation is responsible for filtering the provided assessments 
        to find what it needs, determining the execution status (COMPLETE/PARTIAL/INCONCLUSIVE), 
        and quantifying the business risk_level.
        """
        pass
