"""
FleetGuard Document Interpretation Framework - Base Interpreter
"""

import abc
from typing import List, Tuple, Any
from infrastructure.documents.models import StructuredDocument
from domain.document_interpretation.models import ValidationIssue, BusinessDocumentType


class BaseDocumentInterpreter(abc.ABC):
    """
    Abstract Base Class for FleetGuard Business Document Interpreters.
    Interpreters validate extracted fields against business rules and
    map them into Operational Events.
    """

    @classmethod
    @abc.abstractmethod
    def key(cls) -> str:
        pass

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    @classmethod
    def version(cls) -> str:
        return "1.0.0"
        
    @classmethod
    @abc.abstractmethod
    def get_business_type(cls) -> BusinessDocumentType:
        """
        Returns the specific BusinessDocumentType this interpreter handles.
        """
        pass

    @abc.abstractmethod
    def supports(self, document: StructuredDocument) -> bool:
        """
        Strategy Pattern discovery. Returns True if this interpreter
        is capable of handling the provided StructuredDocument.
        """
        pass

    @abc.abstractmethod
    def validate(self, document: StructuredDocument) -> List[ValidationIssue]:
        """
        Validates the StructuredDocument against business rules.
        Returns a list of ValidationIssues (errors/warnings).
        """
        pass

    @abc.abstractmethod
    def interpret(self, document: StructuredDocument) -> List[Any]:
        """
        Maps the StructuredDocument fields into FleetGuard Operational Events.
        Returns a list of BaseOperationalEvent derivatives.
        """
        pass
