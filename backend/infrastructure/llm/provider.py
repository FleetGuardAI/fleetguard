"""
FleetGuard — LLM Provider Interface
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class LLMMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class LLMResponse(BaseModel):
    message: LLMMessage
    finish_reason: str


class LLMProvider(ABC):
    """Abstract interface for LLM operations."""

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.0,
    ) -> LLMResponse:
        """
        Sends a sequence of messages to the LLM and returns its response.
        If tools are provided, the LLM may elect to call one or more tools.
        """
        pass
