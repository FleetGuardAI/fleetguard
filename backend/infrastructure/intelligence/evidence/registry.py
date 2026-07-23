"""
Fleet Intelligence Engine - Evidence Registry
"""

from typing import Dict, Type, List
from infrastructure.intelligence.evidence.models import BaseEvidence


class EvidenceRegistry:
    """
    Registry for dynamic registration and discovery of evidence types.
    
    This registry is strictly responsible for type registration and lookup.
    It does NOT perform serialization or deserialization.
    """
    
    def __init__(self):
        self._registry: Dict[str, Type[BaseEvidence]] = {}

    def register(self, evidence_class: Type[BaseEvidence]) -> None:
        """
        Registers an evidence class by its evidence_type.
        """
        if not hasattr(evidence_class, 'model_fields') or 'evidence_type' not in evidence_class.model_fields:
             # In Pydantic v2, we check model_fields. 
             pass

        # Since we use strongly typed classes, we can instantiate a dummy to get the default,
        # or we can inspect the model fields. Pydantic v2:
        evidence_type_field = evidence_class.model_fields.get("evidence_type")
        if not evidence_type_field or evidence_type_field.default is None:
            raise ValueError(f"Evidence class {evidence_class.__name__} must define a default evidence_type.")
            
        evidence_type = evidence_type_field.default
        
        if evidence_type in self._registry:
            raise ValueError(f"Evidence type '{evidence_type}' is already registered.")
            
        self._registry[evidence_type] = evidence_class

    def get_class(self, evidence_type: str) -> Type[BaseEvidence]:
        """
        Retrieves the registered class for the given evidence_type.
        Raises ValueError if the type is not registered.
        """
        if evidence_type not in self._registry:
            raise ValueError(f"Evidence type '{evidence_type}' is not registered.")
        return self._registry[evidence_type]

    def enumerate_registered(self) -> List[str]:
        """
        Returns a list of all registered evidence types.
        """
        return list(self._registry.keys())
