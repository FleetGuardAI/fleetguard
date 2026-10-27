"""
FleetGuard — Copilot Schemas
Pydantic models for chat requests/responses, conversations, messages, and pagination.
"""

from datetime import datetime
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
    conversation_id: str = Field(..., description="The canonical conversation ID to use for follow-ups.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata such as tools used or data sources.")


class CreateConversationRequest(BaseModel):
    title: Optional[str] = Field(None, description="Optional title for the conversation.")


class UpdateConversationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Updated conversation title.")


class ConversationMessageOut(BaseModel):
    id: int
    conversation_id: str
    sequence_number: int
    role: str
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    message_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class ConversationOut(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    last_message_preview: Optional[str] = None


class ConversationListResponse(BaseModel):
    conversations: List[ConversationOut]
    total_count: int
    total: int = 0
    limit: int
    offset: int

    def __init__(self, **data):
        if "total" not in data and "total_count" in data:
            data["total"] = data["total_count"]
        elif "total_count" not in data and "total" in data:
            data["total_count"] = data["total"]
        super().__init__(**data)


class ConversationDetailResponse(BaseModel):
    conversation: ConversationOut
    messages: List[ConversationMessageOut]
    id: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __init__(self, **data):
        super().__init__(**data)
        if self.conversation:
            if not self.id:
                self.id = self.conversation.id
            if not self.title:
                self.title = self.conversation.title
            if not self.summary:
                self.summary = self.conversation.summary
            if not self.created_at:
                self.created_at = self.conversation.created_at
            if not self.updated_at:
                self.updated_at = self.conversation.updated_at


class DeleteConversationResponse(BaseModel):
    success: bool = True
    message: str
