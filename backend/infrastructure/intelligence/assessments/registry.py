"""
Fleet Intelligence Engine - Assessment Registry
"""

from typing import Dict, Type, List
from infrastructure.intelligence.assessments.base import BaseAssessment


class AssessmentRegistry:
    """
    Registry for dynamic registration and discovery of intelligence assessments.
    
    This registry is strictly responsible for type registration and lookup.
    It does NOT execute assessments.
    """
    
    def __init__(self):
        self._registry: Dict[str, Type[BaseAssessment]] = {}

    def register(self, assessment_class: Type[BaseAssessment]) -> None:
        """
        Registers an assessment class by its stable key.
        """
        key = assessment_class.key()
        if key in self._registry:
            raise ValueError(f"Assessment '{key}' is already registered.")
            
        self._registry[key] = assessment_class

    def get_assessment(self, assessment_key: str) -> Type[BaseAssessment]:
        """
        Retrieves the registered class for the given assessment_key.
        Raises ValueError if the assessment is not registered.
        """
        if assessment_key not in self._registry:
            raise ValueError(f"Assessment '{assessment_key}' is not registered.")
        return self._registry[assessment_key]

    def enumerate_assessments(self) -> List[Type[BaseAssessment]]:
        """
        Returns a deterministically sorted list of all registered assessment classes.
        Sorts alphabetically by assessment key to guarantee consistent execution order.
        """
        sorted_keys = sorted(self._registry.keys())
        return [self._registry[key] for key in sorted_keys]
