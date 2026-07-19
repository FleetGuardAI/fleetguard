"""
Fleet Intelligence Engine - Base Check
"""

import abc
from typing import List, Type
from infrastructure.intelligence.evidence.models import BaseEvidence
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.checks.models import CheckResult


class BaseCheck(abc.ABC):
    """
    Abstract Base Class for all Intelligence Checks.
    
    Checks are pure, deterministic, and stateless evaluators of facts.
    They must never access databases, external services, or make business
    policy decisions.
    """
    
    @classmethod
    @abc.abstractmethod
    def key(cls) -> str:
        """
        Returns the stable unique identifier of the check (e.g., 'fuel.station_proximity').
        """
        pass

    @classmethod
    def name(cls) -> str:
        """
        Returns the unique name of the check. By default, the class name.
        """
        return cls.__name__

    @classmethod
    @abc.abstractmethod
    def required_evidence(cls) -> List[Type[BaseEvidence]]:
        """
        Declares the evidence types strictly required for this check to execute.
        If any of these are missing in the EvidencePackage, the CheckExecutor 
        will skip execution.
        """
        pass

    @classmethod
    def optional_evidence(cls) -> List[Type[BaseEvidence]]:
        """
        Declares the evidence types that the check can optionally use if present.
        Missing optional evidence does not prevent execution.
        """
        return []

    @abc.abstractmethod
    def execute(self, package: EvidencePackage) -> CheckResult:
        """
        Executes the objective logic against the provided EvidencePackage.
        
        Must return a CheckResult.
        Given identical evidence, this method must always produce the same result.
        """
        pass
