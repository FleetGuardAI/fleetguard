"""
FleetGuard — Copilot Schemas
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class CopilotContext(BaseModel):
    screen: Optional[str] = Field(None, description="The screen the user is currently viewing.")
    entity_type: Optional[str] = Field(None, description="The type of entity (e.g., 'trip', 'vehicle', 'fleet').")
    entity_id: Optional[str] = Field(None, description="The specific ID of the entity.")


class CopilotChatRequest(BaseModel):
    message: str = Field(..., description="The user's message.")
    language: Optional[str] = Field("en", description="Preferred response language (en, hi)")
    conversation_id: Optional[str] = Field(None, description="An optional UUID to continue an existing conversation.")
    context: Optional[CopilotContext] = Field(None, description="Optional context about what the user is currently viewing.")


class CopilotChatResponse(BaseModel):
    message: str = Field(..., description="The grounded natural language response from Copilot.")
    conversation_id: str = Field(..., description="The conversation ID to use for follow-ups.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata such as tools used or data sources.")
