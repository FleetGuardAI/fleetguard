"""
Fleet Intelligence Engine - Base Assessment
"""

import abc
from typing import List
from infrastructure.intelligence.checks.models import CheckResult
from infrastructure.intelligence.assessments.models import AssessmentResult


class BaseAssessment(abc.ABC):
    """
    Abstract Base Class for all Intelligence Assessments.
    
    Assessments interpret groups of related CheckResults into higher-level domain findings.
    They must never access databases, external services, or make business policy decisions.
    """
    
    @classmethod
    @abc.abstractmethod
    def key(cls) -> str:
        """
        Returns the stable unique identifier of the assessment (e.g., 'fuel.transaction_integrity').
        """
        pass

    @classmethod
    def name(cls) -> str:
        """
        Returns the unique human-readable name of the assessment. By default, the class name.
        """
        return cls.__name__

    @classmethod
    def version(cls) -> str:
        """
        Returns the version of this assessment logic.
        """
        return "1.0"

    @classmethod
    @abc.abstractmethod
    def required_checks(cls) -> List[str]:
        """
        Declares the stable check keys strictly required to make a complete assessment.
        """
        pass

    @classmethod
    def optional_checks(cls) -> List[str]:
        """
        Declares the stable check keys that the assessment can optionally use if present.
        """
        return []

    @abc.abstractmethod
    def execute(self, checks: List[CheckResult]) -> AssessmentResult:
        """
        Executes the interpretation logic against the provided CheckResults.
        
        Must return an AssessmentResult.
        Given identical checks, this method must always produce the same result.
        
        The implementation is responsible for determining if the assessment is
        COMPLETE, PARTIAL, or INCONCLUSIVE based on the availability and status
        of the checks provided.
        """
        pass
