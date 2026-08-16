"""
FleetGuard — Copilot Schemas
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class CopilotContext(BaseModel):
    type: str = Field(description="The type of context (e.g., 'trip', 'vehicle', 'fleet').")
    id: Optional[str] = Field(None, description="The specific ID of the entity.")


class CopilotChatRequest(BaseModel):
    message: str = Field(..., description="The user's message.")
    conversation_id: Optional[str] = Field(None, description="An optional UUID to continue an existing conversation.")
    context: Optional[CopilotContext] = Field(None, description="Optional context about what the user is currently viewing.")


class CopilotChatResponse(BaseModel):
    message: str = Field(..., description="The grounded natural language response from Copilot.")
    conversation_id: str = Field(..., description="The conversation ID to use for follow-ups.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata such as tools used or data sources.")
