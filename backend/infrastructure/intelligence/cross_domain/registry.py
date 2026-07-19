"""
Fleet Intelligence Engine - Cross-Domain Registry
"""

from typing import Dict, List, Type
import logging
from infrastructure.intelligence.cross_domain.base import BaseCrossDomainAnalyzer


logger = logging.getLogger(__name__)


class CrossDomainRegistry:
    """
    Registry for Cross-Domain Analyzers.
    Provides deterministic discovery and execution ordering.
    """
    def __init__(self):
        self._analyzers: Dict[str, Type[BaseCrossDomainAnalyzer]] = {}
        # List preserves deterministic execution ordering based on registration
        self._ordered_keys: List[str] = []

    def register(self, analyzer_class: Type[BaseCrossDomainAnalyzer]) -> None:
        """
        Registers an analyzer.
        Raises ValueError if an analyzer with the same key is already registered.
        """
        key = analyzer_class.key()
        if key in self._analyzers:
            raise ValueError(f"Cross-Domain Analyzer with key '{key}' is already registered.")
            
        self._analyzers[key] = analyzer_class
        self._ordered_keys.append(key)
        logger.debug(f"Registered Cross-Domain Analyzer: {key} ({analyzer_class.name()})")

    def get_analyzer(self, key: str) -> Type[BaseCrossDomainAnalyzer]:
        """
        Retrieves a registered analyzer by key.
        Raises KeyError if the analyzer is not found.
        """
        if key not in self._analyzers:
            raise KeyError(f"No Cross-Domain Analyzer found with key '{key}'.")
        return self._analyzers[key]

    def get_all_analyzers(self) -> List[Type[BaseCrossDomainAnalyzer]]:
        """
        Returns all registered analyzers in a deterministic order.
        """
        return [self._analyzers[key] for key in self._ordered_keys]

    def clear(self) -> None:
        """
        Clears all registered analyzers (mostly useful for testing).
        """
        self._analyzers.clear()
        self._ordered_keys.clear()
