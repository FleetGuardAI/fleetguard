"""
FleetGuard — Copilot Router
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status

from services.auth_service import get_current_user
from models.user import User
from database import get_read_uow
from infrastructure.uow import AbstractUnitOfWork
from schemas.copilot import CopilotChatRequest, CopilotChatResponse
from services.copilot_service import CopilotService

router = APIRouter(prefix="/copilot", tags=["Copilot"])
logger = logging.getLogger("fleetguard.routers.copilot")


@router.post(
    "/chat",
    response_model=CopilotChatResponse,
    summary="Interact with Fleet Copilot",
    description="Send a message to the AI copilot. Automatically scopes tools and responses to the authenticated user's fleet."
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
        service = CopilotService(uow=uow, company_id=current_user.company_id)
        response = await service.chat(request)
        return response
    except Exception as e:
        logger.error(f"Error in Copilot chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while communicating with the Copilot service."
        )
