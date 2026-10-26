"""
Tests for Copilot API Endpoint
"""

import pytest
from httpx import AsyncClient, ASGITransport
import uuid

from infrastructure.llm.provider import LLMMessage, LLMResponse
from models.user import User
from main import app

# Mock data
MOCK_COMPANY_ID = 1001
MOCK_USER_ID = uuid.uuid4()
MOCK_TRIP_ID = 101
MOCK_VEHICLE_ID = 201


@pytest.fixture
def mock_openai(monkeypatch):
    class MockOpenAIProvider:
        def __init__(self, *args, **kwargs):
            pass

        async def chat(self, messages, tools=None, temperature=0.0):
            if messages[-1].role == "tool":
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="Here is the grounded response based on the tool data."
                    ),
                    finish_reason="stop"
                )

            last_msg = messages[-1].content
            
            if "fleet doing" in last_msg.lower():
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="",
                        tool_calls=[{
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "get_fleet_summary",
                                "arguments": "{}"
                            }
                        }]
                    ),
                    finish_reason="tool_calls"
                )
            elif "trip" in last_msg.lower():
                return LLMResponse(
                    message=LLMMessage(
                        role="assistant",
                        content="",
                        tool_calls=[{
                            "id": "call_124",
                            "type": "function",
                            "function": {
                                "name": "get_trip_details",
                                "arguments": '{"trip_id": 101}'
                            }
                        }]
                    ),
                    finish_reason="tool_calls"
                )
            
            return LLMResponse(
                message=LLMMessage(
                    role="assistant",
                    content="Hello! How can I help?"
                ),
                finish_reason="stop"
            )

    monkeypatch.setattr("services.copilot_service.OpenAIProvider", MockOpenAIProvider)


@pytest.fixture
def mock_dependencies():
    from services.auth_service import get_current_user
    
    def override_get_current_user():
        u = User(
            email="test@fleetguard.com",
            mobile_number="1234567890",
            password_hash="xxx",
            full_name="Test User",
            is_active=True,
            role="COMPANY_ADMIN"
        )
        u.id = MOCK_USER_ID
        u.company_id = MOCK_COMPANY_ID
        return u

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_copilot_basic_chat(mock_openai, mock_dependencies, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/copilot/chat",
            json={"message": "Hello"}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Hello! How can I help?"
    assert "conversation_id" in data


@pytest.mark.asyncio
async def test_copilot_tool_call_fleet_summary(mock_openai, mock_dependencies, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/copilot/chat",
            json={"message": "How is my fleet doing?"}
        )
    assert response.status_code == 200
    data = response.json()
    assert "grounded response" in data["message"].lower()
    assert "get_fleet_summary" in data["metadata"]["tools_used"]


@pytest.mark.asyncio
async def test_copilot_tool_call_trip(mock_openai, mock_dependencies, db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/copilot/chat",
            json={"message": "Why did this trip lose money?"}
        )
    assert response.status_code == 200
    data = response.json()
    assert "grounded response" in data["message"].lower()
    assert "get_trip_details" in data["metadata"]["tools_used"]


@pytest.mark.asyncio
async def test_copilot_unauthenticated(db_session):
    from services.auth_service import get_current_user
    app.dependency_overrides.pop(get_current_user, None)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/copilot/chat",
            json={"message": "Hello"}
        )
    assert response.status_code == 401
