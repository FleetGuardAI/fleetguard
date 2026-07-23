"""
Audit Framework - Tracking
"""

from typing import List, Optional
from datetime import datetime
from infrastructure.audit.models import AuditRecord
from infrastructure.audit.repository import BaseAuditRepository

class AuditTracker:
    """
    Facade over the repository to support complex chronological retrieval and filtering.
    """
    def __init__(self, repository: BaseAuditRepository):
        self.repository = repository

    def get_history_for_entity(self, entity_type: str, entity_id: str) -> List[AuditRecord]:
        """
        Retrieves the chronological audit history for a specific entity.
        """
        records = self.repository.find_by_entity(entity_type, entity_id)
        # Sort chronologically by timestamp
        return sorted(records, key=lambda r: r.event.timestamp)

    def filter_records(
        self,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        actor_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AuditRecord]:
        """
        Retrieves records matching the provided filters.
        """
        # In a real DB this would be a constructed query. For in-memory we fetch all or filter iteratively.
        # Start with correlation if present since it's highly selective.
        if correlation_id:
            records = self.repository.find_by_correlation(correlation_id)
        elif category:
            records = self.repository.find_by_category(category)
        else:
            # Fallback to all records (depends on repository implementation)
            # For this stub, we'll assume the repo exposes a way to get all if we really needed it, 
            # but ideally we just filter. Let's assume the repo has `_records` or we extend it.
            if hasattr(self.repository, "_records"):
                records = getattr(self.repository, "_records")
            else:
                records = []
                
        # Apply remaining filters
        filtered = []
        for r in records:
            if category and r.event.category.value != category and not correlation_id: 
                # If we searched by correlation_id, we still need to filter category
                if r.event.category.value != category:
                    continue
            if severity and r.event.severity.value != severity:
                continue
            if actor_id and r.event.actor_id != actor_id:
                continue
            if start_time and r.event.timestamp < start_time:
                continue
            if end_time and r.event.timestamp > end_time:
                continue
                
            filtered.append(r)
            
        return sorted(filtered, key=lambda r: r.event.timestamp)
