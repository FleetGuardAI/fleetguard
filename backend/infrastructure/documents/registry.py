"""
Document Intelligence Framework - Registry
"""

from typing import Dict, List, Type
import logging
from infrastructure.documents.base import BaseDocumentParser
from infrastructure.documents.models import DocumentFamily


logger = logging.getLogger(__name__)


class DocumentParserRegistry:
    """
    Registry for structural document parsers.
    Provides deterministic discovery and mapping by DocumentFamily.
    """
    def __init__(self):
        self._parsers_by_key: Dict[str, Type[BaseDocumentParser]] = {}
        # Allows resolving the correct parser by the classified family
        self._parsers_by_family: Dict[DocumentFamily, Type[BaseDocumentParser]] = {}
        self._ordered_keys: List[str] = []

    def register(self, parser_class: Type[BaseDocumentParser]) -> None:
        """
        Registers a document parser.
        Raises ValueError if a parser with the same key or for the same DocumentFamily is already registered.
        """
        key = parser_class.key()
        family = parser_class.supports()
        
        if key in self._parsers_by_key:
            raise ValueError(f"Document Parser with key '{key}' is already registered.")
            
        if family in self._parsers_by_family:
            raise ValueError(f"A Document Parser for family '{family.value}' is already registered.")
            
        self._parsers_by_key[key] = parser_class
        self._parsers_by_family[family] = parser_class
        self._ordered_keys.append(key)
        logger.debug(f"Registered Document Parser: {key} for family {family.value}")

    def get_parser_by_family(self, family: DocumentFamily) -> Type[BaseDocumentParser]:
        """
        Retrieves a registered parser by the DocumentFamily it supports.
        Raises KeyError if the parser is not found.
        """
        if family not in self._parsers_by_family:
            raise KeyError(f"No Document Parser registered for family '{family.value}'.")
        return self._parsers_by_family[family]

    def get_all_parsers(self) -> List[Type[BaseDocumentParser]]:
        """
        Returns all registered parsers in a deterministic order.
        """
        return [self._parsers_by_key[key] for key in self._ordered_keys]

    def clear(self) -> None:
        """
        Clears all registered parsers.
        """
        self._parsers_by_key.clear()
        self._parsers_by_family.clear()
        self._ordered_keys.clear()
