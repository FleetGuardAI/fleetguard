"""
Fleet Intelligence Engine - Evidence Package
"""

from typing import List, Type, TypeVar, Optional, Dict
from infrastructure.intelligence.evidence.models import BaseEvidence

T = TypeVar('T', bound=BaseEvidence)


class EvidencePackage:
    """
    Immutable container representing the complete materialized evidence 
    for one operational event.
    
    This is a READ-ONLY domain object. Duplicate evidence types supplied 
    during construction will result in a fast failure.
    """
    
    def __init__(self, evidence_list: List[BaseEvidence]):
        self._evidence_map: Dict[str, List[BaseEvidence]] = {}
        seen_ids = set()
        
        for ev in evidence_list:
            if ev.evidence_id in seen_ids:
                raise ValueError(
                    f"Duplicate evidence_id detected: {ev.evidence_id}. "
                    "Duplicate resolution must occur before constructing EvidencePackage."
                )
            seen_ids.add(ev.evidence_id)
            
            ev_type = ev.__class__
            if ev_type not in self._evidence_map:
                self._evidence_map[ev_type] = []
            self._evidence_map[ev_type].append(ev)
            
        # Freeze the internal map (dict doesn't support freezing directly in Python, 
        # but we do not expose any mutator methods)

    def get_evidence(self, evidence_type: Type[T]) -> Optional[T]:
        """
        Retrieves the first (or primary) evidence of the requested type if available.
        Returns None gracefully if the evidence is missing.
        """
        ev_list = self._evidence_map.get(evidence_type)
        if ev_list and len(ev_list) > 0:
            return ev_list[0]
        return None

    def get_all_evidence(self, evidence_type: Type[T]) -> List[T]:
        """
        Returns every evidence object of that type.
        """
        return self._evidence_map.get(evidence_type, [])

    def has_evidence(self, evidence_type: Type[BaseEvidence]) -> bool:
        """
        Checks if the requested evidence type exists in the package.
        """
        return evidence_type in self._evidence_map

    def iterate_all(self) -> List[BaseEvidence]:
        """
        Returns a flat list of all instantiated evidence objects across all types.
        """
        flat_list = []
        for ev_list in self._evidence_map.values():
            flat_list.extend(ev_list)
        return flat_list

    def available_types(self) -> List[Type[BaseEvidence]]:
        """
        Returns a list of the currently available evidence types in this package.
        """
        return list(self._evidence_map.keys())

    # Prevent dynamic attribute assignment to enforce immutability
    def __setattr__(self, name, value):
        if name == "_evidence_map" and not hasattr(self, "_evidence_map"):
            super().__setattr__(name, value)
        else:
            raise AttributeError("EvidencePackage is immutable and cannot be modified.")
