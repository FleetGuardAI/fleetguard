"""
FleetGuard — Copilot Router
Provides authenticated endpoints for AI Copilot chat and full conversation history management.
All endpoints strictly enforce tenant and user isolation.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from services.auth_service import get_current_user
from models.user import User
from database import get_read_uow
from infrastructure.uow import AbstractUnitOfWork
from schemas.copilot import (
    CopilotChatRequest,
    CopilotChatResponse,
    CreateConversationRequest,
    UpdateConversationRequest,
    ConversationOut,
    ConversationListResponse,
    ConversationDetailResponse,
    DeleteConversationResponse,
)
from infrastructure.llm.provider import LLMValidationError, LLMServiceUnavailableError
from services.copilot_service import CopilotService


router = APIRouter(prefix="/copilot", tags=["Copilot"])
logger = logging.getLogger("fleetguard.routers.copilot")


@router.post(
    "/chat",
    response_model=CopilotChatResponse,
    summary="Interact with Fleet Copilot",
    description="Send a message to the AI copilot. Automatically scopes tools, history, and memory to the authenticated user's fleet."
)
async def chat_with_copilot(
    request: CopilotChatRequest,
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_read_uow)
) -> CopilotChatResponse:
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a company."
        )

    try:
        service = CopilotService(
            uow=uow,
            company_id=current_user.company_id,
            user_id=current_user.id,
            user_name=current_user.full_name or "Fleet Manager"
        )
        response = await service.chat(request)
        return response
    except PermissionError as pe:
        logger.warning(f"Unauthorized or invalid conversation access: {pe}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or unauthorized access."
        )
    except LLMValidationError as ve:
        logger.error(f"Provider tool schema or argument validation failure: {ve}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI provider could not process the tool parameters for this request. Please try rephrasing your question."
        )
    except LLMServiceUnavailableError as se:
        logger.error(f"LLM provider service unavailable: {se}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The AI service is temporarily unavailable. Please try again in a few moments."
        )
    except RuntimeError as re:
        logger.error(f"Copilot runtime failure: {re}")
        user_msg = str(re)
        if any(marker in user_msg for marker in ("{", "Error code:", "failed_generation", "Traceback", "BadRequestError")):
            user_msg = "The AI service encountered an issue processing tool arguments. Please try again or rephrase your request."
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=user_msg
        )
    except Exception as e:
        logger.error(f"Error in Copilot chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while communicating with the Copilot service. Please try again later."
        )



@router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List Conversations",
    description="Lists persistent conversations for the authenticated user and company, ordered by recent activity."
)
async def list_conversations(
    limit: int = Query(20, ge=1, le=100, description="Max conversations to retrieve"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_read_uow)
) -> ConversationListResponse:
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not associated with a company.")

    service = CopilotService(
        uow=uow,
        company_id=current_user.company_id,
        user_id=current_user.id,
        user_name=current_user.full_name or "Fleet Manager"
    )
    return await service.list_conversations(limit=limit, offset=offset)


@router.post(
    "/conversations",
    response_model=ConversationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Conversation",
    description="Explicitly starts a fresh conversation thread with a unique ID."
)
async def create_conversation(
    request: CreateConversationRequest = CreateConversationRequest(),
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_read_uow)
) -> ConversationOut:
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not associated with a company.")

    service = CopilotService(
        uow=uow,
        company_id=current_user.company_id,
        user_id=current_user.id,
        user_name=current_user.full_name or "Fleet Manager"
    )
    return await service.create_conversation(title=request.title)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get Conversation Detail",
    description="Retrieves a conversation's details and full chronological messages. Strictly scoped to the authenticated user and tenant."
)
async def get_conversation_detail(
    conversation_id: str,
    limit: int = Query(100, ge=1, le=500, description="Max messages to retrieve"),
    offset: int = Query(0, ge=0, description="Message pagination offset"),
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_read_uow)
) -> ConversationDetailResponse:
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not associated with a company.")

    service = CopilotService(
        uow=uow,
        company_id=current_user.company_id,
        user_id=current_user.id,
        user_name=current_user.full_name or "Fleet Manager"
    )
    try:
        return await service.get_conversation_detail(conversation_id, limit=limit, offset=offset)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or unauthorized access.")


@router.patch(
    "/conversations/{conversation_id}",
    response_model=ConversationOut,
    summary="Update Conversation Title",
    description="Updates the title of an existing conversation."
)
async def update_conversation_title(
    conversation_id: str,
    request: UpdateConversationRequest,
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_read_uow)
) -> ConversationOut:
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not associated with a company.")

    service = CopilotService(
        uow=uow,
        company_id=current_user.company_id,
        user_id=current_user.id,
        user_name=current_user.full_name or "Fleet Manager"
    )
    try:
        return await service.update_conversation_title(conversation_id, request.title)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or unauthorized access.")


@router.delete(
    "/conversations/{conversation_id}",
    response_model=DeleteConversationResponse,
    summary="Delete Conversation",
    description="Soft-deletes a conversation and its messages. Enforces strict ownership checks."
)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_read_uow)
) -> DeleteConversationResponse:
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not associated with a company.")

    service = CopilotService(
        uow=uow,
        company_id=current_user.company_id,
        user_id=current_user.id,
        user_name=current_user.full_name or "Fleet Manager"
    )
    try:
        await service.delete_conversation(conversation_id)
        return DeleteConversationResponse(success=True, message="Conversation deleted successfully.")
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found or unauthorized access.")


@router.delete(
    "/conversations",
    response_model=DeleteConversationResponse,
    summary="Clear History",
    description="Clears all conversation history for the authenticated user within their company."
)
async def clear_all_conversations(
    current_user: User = Depends(get_current_user),
    uow: AbstractUnitOfWork = Depends(get_read_uow)
) -> DeleteConversationResponse:
    if not current_user.company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not associated with a company.")

    service = CopilotService(
        uow=uow,
        company_id=current_user.company_id,
        user_id=current_user.id,
        user_name=current_user.full_name or "Fleet Manager"
    )
    count = await service.clear_all_conversations()
    return DeleteConversationResponse(success=True, message=f"Successfully cleared {count} conversations.")
