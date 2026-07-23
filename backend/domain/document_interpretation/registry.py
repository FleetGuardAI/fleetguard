"""
FleetGuard Document Interpretation Framework - Registry
"""

from typing import Dict, List, Type, Optional
import logging
from domain.document_interpretation.base import BaseDocumentInterpreter
from infrastructure.documents.models import StructuredDocument


logger = logging.getLogger(__name__)


class DocumentInterpreterRegistry:
    """
    Registry for Document Interpreters.
    Iterates through registered interpreters to find the appropriate strategy
    using the .supports() method.
    """
    def __init__(self):
        self._interpreters: Dict[str, Type[BaseDocumentInterpreter]] = {}
        self._ordered_keys: List[str] = []

    def register(self, interpreter_class: Type[BaseDocumentInterpreter]) -> None:
        """
        Registers an interpreter.
        Raises ValueError if a parser with the same key is already registered.
        """
        key = interpreter_class.key()
        
        if key in self._interpreters:
            raise ValueError(f"Document Interpreter with key '{key}' is already registered.")
            
        self._interpreters[key] = interpreter_class
        self._ordered_keys.append(key)
        logger.debug(f"Registered Document Interpreter: {key}")

    def find_interpreter(self, document: StructuredDocument) -> Optional[BaseDocumentInterpreter]:
        """
        Finds the first registered interpreter that supports the document.
        Returns an instance of the interpreter, or None if no match is found.
        """
        for key in self._ordered_keys:
            interpreter_class = self._interpreters[key]
            interpreter_instance = interpreter_class()
            if interpreter_instance.supports(document):
                return interpreter_instance
                
        return None

    def clear(self) -> None:
        """
        Clears all registered interpreters.
        """
        self._interpreters.clear()
        self._ordered_keys.clear()
