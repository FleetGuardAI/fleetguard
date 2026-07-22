"""
Audit Framework - Repository
"""

import abc
import uuid
from typing import List, Optional
from infrastructure.audit.models import AuditRecord

class BaseAuditRepository(abc.ABC):
    """
    Abstract append-only repository for audit records.
    Update and delete methods are deliberately omitted.
    """
    
    @abc.abstractmethod
    def save(self, record: AuditRecord) -> None:
        pass
        
    @abc.abstractmethod
    def save_batch(self, records: List[AuditRecord]) -> None:
        pass
        
    @abc.abstractmethod
    def find_by_id(self, audit_id: uuid.UUID) -> Optional[AuditRecord]:
        pass
        
    @abc.abstractmethod
    def find_by_entity(self, entity_type: str, entity_id: str) -> List[AuditRecord]:
        pass
        
    @abc.abstractmethod
    def find_by_category(self, category: str) -> List[AuditRecord]:
        pass
        
    @abc.abstractmethod
    def find_by_correlation(self, correlation_id: str) -> List[AuditRecord]:
        pass


class InMemoryAuditRepository(BaseAuditRepository):
    """
    In-memory append-only repository implementation.
    """
    def __init__(self):
        self._records: List[AuditRecord] = []

    def save(self, record: AuditRecord) -> None:
        self._records.append(record)
        
    def save_batch(self, records: List[AuditRecord]) -> None:
        self._records.extend(records)
        
    def find_by_id(self, audit_id: uuid.UUID) -> Optional[AuditRecord]:
        for r in self._records:
            if r.event.audit_id == audit_id:
                return r
        return None
        
    def find_by_entity(self, entity_type: str, entity_id: str) -> List[AuditRecord]:
        return [r for r in self._records if r.event.entity_type == entity_type and r.event.entity_id == entity_id]
        
    def find_by_category(self, category: str) -> List[AuditRecord]:
        return [r for r in self._records if r.event.category.value == category]
        
    def find_by_correlation(self, correlation_id: str) -> List[AuditRecord]:
        return [r for r in self._records if r.event.correlation_id == correlation_id]
