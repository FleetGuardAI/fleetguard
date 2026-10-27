"""
FleetGuard — Copilot Conversation & Message Models
Persists conversational threads, messages, structured metadata, and rolling summaries
scoped strictly to user and tenant (company).
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Conversation(Base):
    """
    Represents an ongoing or historical conversation session with the AI Co-Pilot.
    Strictly isolated by user_id and company_id.
    """
    __tablename__ = "copilot_conversations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # Canonical UUID string
    company_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New Conversation")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.sequence_number"
    )


class ConversationMessage(Base):
    """
    Represents an individual message (user, assistant, or tool) within a conversation.
    """
    __tablename__ = "copilot_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("copilot_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user', 'assistant', 'system', 'tool'
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Tool name or user name
    tool_call_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # For tool result messages
    tool_calls: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)  # Assistant tool calls
    message_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)  # Structured cards, proposals, etc.

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationship
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")
