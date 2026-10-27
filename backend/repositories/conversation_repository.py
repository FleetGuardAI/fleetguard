"""
FleetGuard — Conversation Repository
Data access layer for Copilot Conversations and Messages.
Enforces multi-tenancy (company_id) and user scoping on all operations.
"""

from datetime import datetime, timezone
from typing import Optional, Sequence, List, Dict, Any, Tuple
from sqlalchemy import select, update, desc, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models.conversation import Conversation, ConversationMessage


class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_conversation(
        self,
        conversation_id: str,
        user_id: int,
        company_id: int,
        include_messages: bool = False
    ) -> Optional[Conversation]:
        """
        Retrieves a conversation strictly verified by user_id and company_id.
        Optionally preloads messages ordered by sequence_number.
        """
        stmt = (
            select(Conversation)
            .where(
                Conversation.id == str(conversation_id),
                Conversation.user_id == int(user_id),
                Conversation.company_id == int(company_id),
                Conversation.is_deleted == False
            )
        )
        if include_messages:
            stmt = stmt.options(selectinload(Conversation.messages))
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_conversations(
        self,
        user_id: int,
        company_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[Sequence[Conversation], int]:
        """
        Lists active conversations for user within company, ordered by updated_at descending.
        Returns (conversations, total_count).
        """
        base_filter = [
            Conversation.user_id == int(user_id),
            Conversation.company_id == int(company_id),
            Conversation.is_deleted == False
        ]
        count_stmt = select(func.count(Conversation.id)).where(*base_filter)
        total_count = (await self.db.execute(count_stmt)).scalar_one_or_none() or 0

        stmt = (
            select(Conversation)
            .where(*base_filter)
            .order_by(desc(Conversation.updated_at))
            .limit(limit)
            .offset(offset)
        )
        res = await self.db.execute(stmt)
        return res.scalars().all(), total_count

    async def create_conversation(
        self,
        conversation_id: str,
        user_id: int,
        company_id: int,
        title: str = "New Conversation"
    ) -> Conversation:
        """Creates a new conversation record."""
        conv = Conversation(
            id=str(conversation_id),
            user_id=int(user_id),
            company_id=int(company_id),
            title=title[:255]
        )
        self.db.add(conv)
        await self.db.flush()
        return conv

    async def update_title(
        self,
        conversation_id: str,
        user_id: int,
        company_id: int,
        new_title: str
    ) -> Optional[Conversation]:
        """Updates the conversation title."""
        conv = await self.get_conversation(conversation_id, user_id, company_id)
        if conv:
            conv.title = new_title[:255]
            conv.updated_at = datetime.now(timezone.utc)
            await self.db.flush()
        return conv

    async def update_summary(
        self,
        conversation_id: str,
        user_id: int,
        company_id: int,
        summary: str
    ) -> Optional[Conversation]:
        """Updates the rolling summary for older conversation context."""
        conv = await self.get_conversation(conversation_id, user_id, company_id)
        if conv:
            conv.summary = summary
            conv.summary_updated_at = datetime.now(timezone.utc)
            await self.db.flush()
        return conv

    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: int,
        company_id: int
    ) -> bool:
        """Soft-deletes a conversation strictly scoped to user and company."""
        conv = await self.get_conversation(conversation_id, user_id, company_id)
        if not conv:
            return False
        conv.is_deleted = True
        conv.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def clear_all_conversations(
        self,
        user_id: int,
        company_id: int
    ) -> int:
        """Soft-deletes all conversations for this user within company."""
        stmt = (
            update(Conversation)
            .where(
                Conversation.user_id == int(user_id),
                Conversation.company_id == int(company_id),
                Conversation.is_deleted == False
            )
            .values(is_deleted=True, updated_at=datetime.now(timezone.utc))
        )
        res = await self.db.execute(stmt)
        await self.db.flush()
        return res.rowcount

    async def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> Sequence[ConversationMessage]:
        """Retrieves chronological messages for a conversation."""
        stmt = (
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == str(conversation_id))
            .order_by(ConversationMessage.sequence_number.asc())
        )
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)
        res = await self.db.execute(stmt)
        return res.scalars().all()

    async def get_next_sequence_number(self, conversation_id: str) -> int:
        """Determines the next monotonic sequence number for messages in a conversation."""
        stmt = (
            select(func.coalesce(func.max(ConversationMessage.sequence_number), 0))
            .where(ConversationMessage.conversation_id == str(conversation_id))
        )
        max_seq = (await self.db.execute(stmt)).scalar_one_or_none() or 0
        return int(max_seq) + 1

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        name: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        message_metadata: Optional[Dict[str, Any]] = None,
        sequence_number: Optional[int] = None
    ) -> ConversationMessage:
        """Appends a new chronological message to the conversation."""
        if sequence_number is None:
            sequence_number = await self.get_next_sequence_number(conversation_id)

        msg = ConversationMessage(
            conversation_id=str(conversation_id),
            sequence_number=sequence_number,
            role=role,
            content=content or "",
            name=name,
            tool_call_id=tool_call_id,
            tool_calls=tool_calls,
            message_metadata=message_metadata
        )
        self.db.add(msg)
        # Touch conversation updated_at
        conv_stmt = (
            update(Conversation)
            .where(Conversation.id == str(conversation_id))
            .values(updated_at=datetime.now(timezone.utc))
        )
        await self.db.execute(conv_stmt)
        await self.db.flush()
        return msg
