"""
Fleet Intelligence Engine - Check Registry
"""

from typing import Dict, Type, List
from infrastructure.intelligence.checks.base import BaseCheck


class CheckRegistry:
    """
    Registry for dynamic registration and discovery of intelligence checks.
    
    This registry is strictly responsible for type registration and lookup.
    It does NOT execute checks.
    """
    
    def __init__(self):
        self._registry: Dict[str, Type[BaseCheck]] = {}

    def register(self, check_class: Type[BaseCheck]) -> None:
        """
        Registers a check class by its name.
        """
        name = check_class.name()
        if name in self._registry:
            raise ValueError(f"Check '{name}' is already registered.")
            
        self._registry[name] = check_class

    def get_check(self, check_name: str) -> Type[BaseCheck]:
        """
        Retrieves the registered class for the given check_name.
        Raises ValueError if the check is not registered.
        """
        if check_name not in self._registry:
            raise ValueError(f"Check '{check_name}' is not registered.")
        return self._registry[check_name]

    def enumerate_checks(self) -> List[Type[BaseCheck]]:
        """
        Returns a deterministically sorted list of all registered check classes.
        Sorts alphabetically by check name to guarantee consistent execution order.
        """
        # Sort by check name alphabetically for determinism
        sorted_names = sorted(self._registry.keys())
        return [self._registry[name] for name in sorted_names]
