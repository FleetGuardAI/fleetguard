"""
Fleet Intelligence Engine - Domain Risk Registry
"""

from typing import Dict, Type, List
from infrastructure.intelligence.domain_risk.base import BaseDomainRiskEngine


class DomainRiskRegistry:
    """
    Registry for dynamic registration and discovery of domain risk engines.
    
    This registry is strictly responsible for type registration and lookup.
    It does NOT execute risk engines.
    """
    
    def __init__(self):
        self._registry: Dict[str, Type[BaseDomainRiskEngine]] = {}

    def register(self, engine_class: Type[BaseDomainRiskEngine]) -> None:
        """
        Registers a domain risk engine class by its stable key.
        """
        key = engine_class.key()
        if key in self._registry:
            raise ValueError(f"Domain risk engine '{key}' is already registered.")
            
        self._registry[key] = engine_class

    def get_engine(self, engine_key: str) -> Type[BaseDomainRiskEngine]:
        """
        Retrieves the registered class for the given engine_key.
        Raises ValueError if the engine is not registered.
        """
        if engine_key not in self._registry:
            raise ValueError(f"Domain risk engine '{engine_key}' is not registered.")
        return self._registry[engine_key]

    def enumerate_engines(self) -> List[Type[BaseDomainRiskEngine]]:
        """
        Returns a deterministically sorted list of all registered engine classes.
        Sorts alphabetically by engine key to guarantee consistent execution order.
        """
        sorted_keys = sorted(self._registry.keys())
        return [self._registry[key] for key in sorted_keys]
