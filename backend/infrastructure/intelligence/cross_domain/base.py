"""
Fleet Intelligence Engine - Base Cross Domain Analyzer
"""

import abc
from typing import List
from infrastructure.intelligence.domain_risk.models import DomainRiskProfile
from infrastructure.intelligence.cross_domain.models import FleetInsight


class BaseCrossDomainAnalyzer(abc.ABC):
    """
    Abstract Base Class for all Cross-Domain Analyzers.
    
    Cross-Domain Analyzers consume DomainRiskProfiles to discover deterministic
    relationships between independent operational domains. They must never calculate
    domain risks, modify recommendations, or access Evidence directly.
    """
    
    @classmethod
    @abc.abstractmethod
    def key(cls) -> str:
        """
        Returns the stable unique identifier of the analyzer (e.g., 'cross.fuel_driver').
        """
        pass

    @classmethod
    def name(cls) -> str:
        """
        Returns the unique human-readable name of the analyzer. By default, the class name.
        """
        return cls.__name__

    @classmethod
    def version(cls) -> str:
        """
        Returns the version of this analyzer logic.
        """
        return "1.0.0"

    @abc.abstractmethod
    def execute(self, profiles: List[DomainRiskProfile]) -> List[FleetInsight]:
        """
        Executes the cross-domain analysis logic against the provided DomainRiskProfiles.
        
        Must return a list of FleetInsights (can be empty if no insights are discovered).
        Given identical profiles, this method must always produce the same result.
        
        The implementation is responsible for extracting the required DomainRiskProfiles 
        from the input list and evaluating relationships deterministically.
        """
        pass
