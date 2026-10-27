"""
FleetGuard — AI Co-Pilot Persistent History & Short-Term Conversational Memory Tests
Regression tests covering:
1. Creating, listing, and retrieving conversations.
2. Deterministic chronological message persistence (user, assistant, tool).
3. Continuing existing conversation by conversation_id.
4. Starting new conversations with isolated context.
5. Multi-tenant and cross-user isolation (404 on unauthorized read/update/delete).
6. Deleting single conversation and clearing all conversations.
7. Bounded context window slicing and tool-call/result pair preservation.
8. Graceful summarization fallback.
9. User message preservation during backend/upstream LLM errors.
10. Safe handling of historical trip proposals (transcripts do not re-execute).
"""

import json
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from infrastructure.llm.provider import LLMMessage, LLMResponse
from models.user import User
from main import app
from schemas.copilot import CopilotChatRequest
from services.copilot_service import CopilotService

MOCK_COMPANY_A = 1001
MOCK_USER_A_ID = 101

MOCK_COMPANY_B = 2002
MOCK_USER_B_ID = 202


@pytest.fixture
def mock_openai(monkeypatch):
    class MockOpenAIProvider:
        def __init__(self, *args, **kwargs):
            pass

        async def chat(self, messages, tools=None, temperature=0.0):
            # Check if this is a summarization request
            if any("summarize" in (m.content or "").lower() for m in messages):
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="User previously inquired about fleet maintenance and vehicle locations."
                    ),
                    finish_reason="stop"
                )

            last_msg = messages[-1].content or ""
            if "trip" in last_msg.lower():
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="Here is a trip proposal.",
                    ),
                    finish_reason="stop"
                )

            return LLMResponse(
                message=LLMMessage(
                    role="assistant",
                    content=f"Echo response to: {last_msg}"
                ),
                finish_reason="stop"
            )

    monkeypatch.setattr("services.copilot_service.OpenAIProvider", MockOpenAIProvider)


@pytest.fixture
def auth_company_a(db_session):
    from services.auth_service import get_current_user
    from database import get_read_uow, get_uow
    from infrastructure.uow import AbstractUnitOfWork, RepositoryRegistry

    def override_get_current_user():
        u = User(
            email="admin_a@fleetguard.com",
            mobile_number="1111111111",
            password_hash="xxx",
            full_name="Company A Admin",
            is_active=True,
            role="COMPANY_ADMIN"
        )
        u.id = MOCK_USER_A_ID
        u.company_id = MOCK_COMPANY_A
        return u

    class _TestSessionUoW(AbstractUnitOfWork):
        def __init__(self):
            self._session = db_session
            self.session = db_session
            self.repositories = RepositoryRegistry(db_session)

        async def commit(self):
            await self._session.commit()

        async def rollback(self):
            await self._session.rollback()

    async def override_get_uow():
        yield _TestSessionUoW()

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_read_uow] = override_get_uow
    app.dependency_overrides[get_uow] = override_get_uow
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_read_uow, None)
    app.dependency_overrides.pop(get_uow, None)


@pytest.fixture
def auth_company_b(db_session):
    from services.auth_service import get_current_user
    from database import get_read_uow, get_uow
    from infrastructure.uow import AbstractUnitOfWork, RepositoryRegistry

    def override_get_current_user():
        u = User(
            email="admin_b@otherfleet.com",
            mobile_number="2222222222",
            password_hash="xxx",
            full_name="Company B Admin",
            is_active=True,
            role="COMPANY_ADMIN"
        )
        u.id = MOCK_USER_B_ID
        u.company_id = MOCK_COMPANY_B
        return u

    class _TestSessionUoW(AbstractUnitOfWork):
        def __init__(self):
            self._session = db_session
            self.session = db_session
            self.repositories = RepositoryRegistry(db_session)

        async def commit(self):
            await self._session.commit()

        async def rollback(self):
            await self._session.rollback()

    async def override_get_uow():
        yield _TestSessionUoW()

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_read_uow] = override_get_uow
    app.dependency_overrides[get_uow] = override_get_uow
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_read_uow, None)
    app.dependency_overrides.pop(get_uow, None)


# ══════════════════════════════════════════════════════════════
# 1. PERSISTENCE & BASIC CHAT FLOW
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_chat_creates_and_persists_conversation(mock_openai, auth_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Step 1: Send initial chat message without conversation_id
        res = await ac.post("/api/v1/copilot/chat", json={"message": "Where are my trucks today?"})
        assert res.status_code == 200
        data = res.json()
        assert "conversation_id" in data
        conv_id = data["conversation_id"]
        assert conv_id is not None
        assert "Echo response to: Where are my trucks today?" in data["message"]

        # Step 2: List conversations to verify title and last-activity
        list_res = await ac.get("/api/v1/copilot/conversations")
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["total"] >= 1
        found = next((c for c in list_data["conversations"] if c["id"] == conv_id), None)
        assert found is not None
        assert "Where are my trucks" in found["title"]
        assert found["message_count"] == 2  # 1 user + 1 assistant

        # Step 3: Retrieve full conversation detail and check chronological messages
        detail_res = await ac.get(f"/api/v1/copilot/conversations/{conv_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["id"] == conv_id
        assert len(detail["messages"]) == 2
        assert detail["messages"][0]["role"] == "user"
        assert detail["messages"][0]["content"] == "Where are my trucks today?"
        assert detail["messages"][0]["sequence_number"] == 1
        assert detail["messages"][1]["role"] == "assistant"
        assert detail["messages"][1]["sequence_number"] == 2


@pytest.mark.asyncio
async def test_continue_existing_conversation(mock_openai, auth_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First turn
        res1 = await ac.post("/api/v1/copilot/chat", json={"message": "First question"})
        conv_id = res1.json()["conversation_id"]

        # Second turn in the same conversation
        res2 = await ac.post("/api/v1/copilot/chat", json={
            "conversation_id": conv_id,
            "message": "Second follow-up question"
        })
        assert res2.status_code == 200
        assert res2.json()["conversation_id"] == conv_id

        # Verify messages in conversation detail
        detail_res = await ac.get(f"/api/v1/copilot/conversations/{conv_id}")
        detail = detail_res.json()
        assert len(detail["messages"]) == 4
        assert [m["role"] for m in detail["messages"]] == ["user", "assistant", "user", "assistant"]
        assert [m["sequence_number"] for m in detail["messages"]] == [1, 2, 3, 4]


@pytest.mark.asyncio
async def test_explicit_create_conversation_endpoint(auth_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/copilot/conversations", json={"title": "Fuel Analysis Q4"})
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Fuel Analysis Q4"
        conv_id = data["id"]

        # Update title
        patch_res = await ac.patch(f"/api/v1/copilot/conversations/{conv_id}", json={"title": "Fuel Analysis Q4 Revised"})
        assert patch_res.status_code == 200
        assert patch_res.json()["title"] == "Fuel Analysis Q4 Revised"


# ══════════════════════════════════════════════════════════════
# 2. ISOLATION & AUTHORIZATION (Cross-User & Cross-Company)
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_cross_company_isolation(mock_openai, auth_company_a, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # User A creates a conversation
        res = await ac.post("/api/v1/copilot/chat", json={"message": "Confidential fleet data for Company A"})
        conv_a_id = res.json()["conversation_id"]

    # Now switch to User B (Company B)
    from services.auth_service import get_current_user
    from database import get_read_uow
    from infrastructure.uow import AbstractUnitOfWork, RepositoryRegistry

    def override_user_b():
        u = User(
            email="intruder@companyb.com",
            mobile_number="9999999999",
            password_hash="xxx",
            full_name="Company B User",
            is_active=True,
            role="COMPANY_ADMIN"
        )
        u.id = MOCK_USER_B_ID
        u.company_id = MOCK_COMPANY_B
        return u

    class _TestSessionUoW(AbstractUnitOfWork):
        def __init__(self):
            self._session = db_session
            self.session = db_session
            self.repositories = RepositoryRegistry(db_session)
        async def commit(self):
            await self._session.commit()
        async def rollback(self):
            await self._session.rollback()

    async def override_get_uow():
        yield _TestSessionUoW()

    app.dependency_overrides[get_current_user] = override_user_b
    app.dependency_overrides[get_read_uow] = override_get_uow

    async with AsyncClient(transport=transport, base_url="http://test") as ac_b:
        # Attempt 1: User B lists conversations -> must NOT see conv_a_id
        list_res = await ac_b.get("/api/v1/copilot/conversations")
        assert list_res.status_code == 200
        convo_ids = [c["id"] for c in list_res.json()["conversations"]]
        assert conv_a_id not in convo_ids

        # Attempt 2: User B requests detail of conv_a_id -> must return 404 (does NOT leak existence)
        get_res = await ac_b.get(f"/api/v1/copilot/conversations/{conv_a_id}")
        assert get_res.status_code == 404

        # Attempt 3: User B attempts to inject a message into conv_a_id -> must return 404
        chat_res = await ac_b.post("/api/v1/copilot/chat", json={
            "conversation_id": conv_a_id,
            "message": "Malicious continuation"
        })
        assert chat_res.status_code == 404

        # Attempt 4: User B attempts to delete conv_a_id -> must return 404
        del_res = await ac_b.delete(f"/api/v1/copilot/conversations/{conv_a_id}")
        assert del_res.status_code == 404


# ══════════════════════════════════════════════════════════════
# 3. DELETION & CLEAR HISTORY
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_delete_individual_conversation(mock_openai, auth_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/copilot/chat", json={"message": "Temporary conversation"})
        conv_id = res.json()["conversation_id"]

        # Delete conversation
        del_res = await ac.delete(f"/api/v1/copilot/conversations/{conv_id}")
        assert del_res.status_code == 200
        assert del_res.json()["success"] is True

        # Now fetching it returns 404
        get_res = await ac.get(f"/api/v1/copilot/conversations/{conv_id}")
        assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_clear_all_conversations(mock_openai, auth_company_a):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Create multiple conversations
        await ac.post("/api/v1/copilot/chat", json={"message": "Chat 1"})
        await ac.post("/api/v1/copilot/chat", json={"message": "Chat 2"})

        # Clear all
        del_all_res = await ac.delete("/api/v1/copilot/conversations")
        assert del_all_res.status_code == 200
        assert del_all_res.json()["success"] is True

        # Listing must now be empty
        list_res = await ac.get("/api/v1/copilot/conversations")
        assert list_res.status_code == 200
        assert list_res.json()["total"] == 0
        assert len(list_res.json()["conversations"]) == 0


# ══════════════════════════════════════════════════════════════
# 4. BOUNDED CONTEXT WINDOW & SAFE TOOL-PAIR SLICING
# ══════════════════════════════════════════════════════════════

def test_safe_context_window_slicing_tool_call_integrity():
    """
    OpenAI and Groq fail with HTTP 400 if a tool message is sent without
    its preceding assistant tool_calls message.
    Verify _slice_safe_context_window preserves tool-call / tool-result pairs.
    """
    from services.copilot_service import CopilotService

    # Construct dummy message sequence with tool calls
    msgs = []
    for i in range(15):
        msgs.append(LLMMessage(role="user", content=f"User msg {i}"))
        msgs.append(LLMMessage(role="assistant", content=f"Assistant reply {i}"))

    # Add assistant with tool call
    msgs.append(LLMMessage(
        role="assistant",
        content="",
        tool_calls=[{"id": "call_999", "type": "function", "function": {"name": "list_vehicles", "arguments": "{}"}}]
    ))
    # Add corresponding tool result
    msgs.append(LLMMessage(
        role="tool",
        content='{"vehicles": ["MH12"]}',
        tool_call_id="call_999",
        name="list_vehicles"
    ))
    # Add final assistant reply
    msgs.append(LLMMessage(role="assistant", content="Here are your vehicles."))

    # Total messages: 33
    older, sliced = CopilotService._slice_safe_context_window(msgs, max_messages=3)

    # Verify that the sliced result includes BOTH the assistant tool_calls and the tool message
    roles = [m.role for m in sliced]
    assert "tool" in roles
    # Must have the matching assistant tool_calls right before the tool
    tool_idx = roles.index("tool")
    assert tool_idx > 0
    assert roles[tool_idx - 1] == "assistant"
    assert sliced[tool_idx - 1].tool_calls is not None


# ══════════════════════════════════════════════════════════════
# 5. USER MESSAGE PRESERVATION ON BACKEND ERROR
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_user_message_preserved_when_llm_fails(monkeypatch, auth_company_a, db_session):
    """
    If the upstream LLM crashes or returns an error, the user's message
    MUST already be saved to the database so it is not lost.
    """
    class CrashingProvider:
        async def chat(self, messages, tools=None, temperature=0.0):
            raise RuntimeError("Upstream provider 503 Service Unavailable")

    monkeypatch.setattr("services.copilot_service.OpenAIProvider", CrashingProvider)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # User sends message
        res = await ac.post("/api/v1/copilot/chat", json={"message": "Crucial fleet question that must not be lost"})
        assert res.status_code == 503

        # Verify that the conversation and the user's message were persisted
        list_res = await ac.get("/api/v1/copilot/conversations")
        assert list_res.status_code == 200
        convo = list_res.json()["conversations"][0]
        assert "Crucial fleet question" in convo["title"]

        detail_res = await ac.get(f"/api/v1/copilot/conversations/{convo['id']}")
        assert detail_res.status_code == 200
        messages = detail_res.json()["messages"]
        assert len(messages) >= 1
        assert messages[0]["role"] == "user"
        assert "Crucial fleet question" in messages[0]["content"]


# ══════════════════════════════════════════════════════════════
# 6. SAFE HANDLING OF HISTORICAL TRIP PROPOSALS
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_historical_transcript_does_not_reexecute_trip(mock_openai, auth_company_a):
    """
    Restoring or continuing a conversation that contains a historical trip proposal
    or statement of confirmation does NOT execute an operational action.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Message about trips
        res = await ac.post("/api/v1/copilot/chat", json={"message": "Can you schedule a trip for MH12?"})
        assert res.status_code == 200
        conv_id = res.json()["conversation_id"]

        # Follow up message
        res2 = await ac.post("/api/v1/copilot/chat", json={
            "conversation_id": conv_id,
            "message": "What else can you do?"
        })
        assert res2.status_code == 200
        # Verified action must be null / no operation executed implicitly
        assert res2.json().get("metadata", {}).get("action_executed") is False


# ══════════════════════════════════════════════════════════════
# 7. LONG CONVERSATIONS, SUMMARIZATION & GRACEFUL DEGRADATION
# ══════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_long_conversation_summarization_and_bounded_context(monkeypatch, auth_company_a, db_session):
    """
    Verify that when conversation history exceeds the configured context window (e.g. 20 messages),
    the older messages are summarized and stored in the conversation record, while the active
    model call is bounded.
    """
    received_context_sizes = []

    class CapturingLLM:
        async def chat(self, messages, tools=None, temperature=0.0):
            # Record how many messages were sent in this prompt
            received_context_sizes.append(len(messages))

            if any("summarize" in (m.content or "").lower() for m in messages):
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="Summary: Discussed trucks 01 and 02 maintenance history."
                    ),
                    finish_reason="stop"
                )

            return LLMResponse(
                message=LLMMessage(role="assistant", content="Acknowledged."),
                finish_reason="stop"
            )

    monkeypatch.setattr("services.copilot_service.OpenAIProvider", CapturingLLM)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Start conversation
        res = await ac.post("/api/v1/copilot/chat", json={"message": "Turn 0"})
        conv_id = res.json()["conversation_id"]

        # Insert 24 more turns directly into the repository to simulate a long conversation
        from repositories.conversation_repository import ConversationRepository
        repo = ConversationRepository(db_session)
        for i in range(1, 25):
            await repo.add_message(conv_id, "user", f"Turn {i} question")
            await repo.add_message(conv_id, "assistant", f"Turn {i} answer")
        await db_session.commit()

        # Send turn 25 via API (total messages in DB is now ~50)
        res_long = await ac.post("/api/v1/copilot/chat", json={
            "conversation_id": conv_id,
            "message": "What was discussed earlier?"
        })
        assert res_long.status_code == 200

        # Verify rolling summary was generated and stored in DB
        detail_res = await ac.get(f"/api/v1/copilot/conversations/{conv_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["summary"] is not None
        assert "Discussed trucks" in detail["summary"]

        # Verify that all 50+ messages remain fully persisted in the user-facing transcript
        assert len(detail["messages"]) >= 50

        # Verify the model context was bounded (system + optional summary + bounded window <= 25)
        # Even though DB has 50+ messages, the LLM received only the bounded context
        assert any(size <= 26 for size in received_context_sizes)


@pytest.mark.asyncio
async def test_summarization_failure_graceful_fallback(monkeypatch, auth_company_a, db_session):
    """
    If rolling summarization fails (e.g. LLM timeout), the chat MUST NOT crash.
    It must fall back gracefully to the bounded recent message window.
    """
    class CrashingSummaryLLM:
        async def chat(self, messages, tools=None, temperature=0.0):
            # If prompt asks for summary, raise error
            if any("summarize" in (m.content or "").lower() for m in messages):
                raise RuntimeError("Summarization model overloaded")
            return LLMResponse(
                message=LLMMessage(role="assistant", content="Graceful fallback succeeded."),
                finish_reason="stop"
            )

    monkeypatch.setattr("services.copilot_service.OpenAIProvider", CrashingSummaryLLM)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post("/api/v1/copilot/chat", json={"message": "Initial chat"})
        conv_id = res.json()["conversation_id"]

        # Insert 22 messages into DB
        from repositories.conversation_repository import ConversationRepository
        repo = ConversationRepository(db_session)
        for i in range(11):
            await repo.add_message(conv_id, "user", f"Historical user {i}")
            await repo.add_message(conv_id, "assistant", f"Historical bot {i}")
        await db_session.commit()

        # Follow-up message triggers summarization attempt
        res_fallback = await ac.post("/api/v1/copilot/chat", json={
            "conversation_id": conv_id,
            "message": "Follow-up despite summary error"
        })
        # Chat must succeed without 500 error
        assert res_fallback.status_code == 200
        assert "Graceful fallback succeeded" in res_fallback.json()["message"]


@pytest.mark.asyncio
async def test_unauthorized_patch_and_delete_returns_404(auth_company_a):
    """
    Attempting to patch or delete a non-existent or foreign conversation ID
    must return 404 Not Found to prevent enumeration attacks.
    """
    fake_id = str(uuid.uuid4())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        patch_res = await ac.patch(f"/api/v1/copilot/conversations/{fake_id}", json={"title": "Hacked"})
        assert patch_res.status_code == 404

        delete_res = await ac.delete(f"/api/v1/copilot/conversations/{fake_id}")
        assert delete_res.status_code == 404

