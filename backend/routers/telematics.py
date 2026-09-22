"""
FleetGuard — Telematics Webhook Router
Handles hardware GPS payloads.
"""
from typing import Annotated, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Security, Request, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings
from database import get_db
from schemas.telematics import NormalizedHardwareEvent, TelematicsBatchResponse
from services.location_service import LocationService

router = APIRouter(
    prefix="/api/v1/tracking/telematics",
    tags=["Hardware Telematics"],
)

webhook_header = APIKeyHeader(name="X-Telematics-Secret", auto_error=False)

def verify_telematics_secret(
    request: Request,
    api_key_header: str = Security(webhook_header)
) -> bool:
    """
    Validates the hardware provider webhook secret.
    """
    settings: Settings = request.app.state.settings
    if not settings.TELEMATICS_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telematics ingestion not configured"
        )
    
    if api_key_header != settings.TELEMATICS_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid telematics secret"
        )
    return True


@router.post(
    "/webhook",
    response_model=TelematicsBatchResponse,
    dependencies=[Depends(verify_telematics_secret)],
    status_code=status.HTTP_200_OK
)
async def process_hardware_telematics(
    request: Request,
    payload: List[NormalizedHardwareEvent],
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest a batch of hardware GPS locations.
    """
    settings: Settings = request.app.state.settings
    
    result = await LocationService.process_hardware_batch(
        db=db,
        locations=payload,
        allow_registration_only=settings.ALLOW_REGISTRATION_ONLY_TELEMATICS
    )
    
    await db.commit()
    return result
