"""
FleetGuard — Driver Vehicle Inspection Router

Pre-trip and post-trip vehicle checklist inspection reports.
Automatically generates maintenance tickets for failed items.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.vehicle_inspection import VehicleInspection, InspectionType, InspectionStatus
from models.ticket import Ticket, TicketStatus, RiskLevel

logger = logging.getLogger("fleetguard.inspection")

router = APIRouter(prefix="/api/v1/driver-app", tags=["Driver Inspection"])


# --- Schemas ---

class InspectionItem(BaseModel):
    name: str  # Tyres, Brakes, Mirrors, Horn, Lights, Leaks, Battery
    passed: bool
    notes: Optional[str] = None
    photo_url: Optional[str] = None


class InspectionCreateRequest(BaseModel):
    driver_id: int
    vehicle_id: int
    company_id: int
    inspection_type: str  # PRE_TRIP or POST_TRIP
    items: List[InspectionItem]
    notes: Optional[str] = None


class InspectionResponse(BaseModel):
    id: int
    driver_id: int
    vehicle_id: int
    company_id: int
    inspection_type: str
    overall_status: str
    items: List[Dict[str, Any]]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("/inspections", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
async def submit_inspection(
    payload: InspectionCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a pre-trip or post-trip vehicle inspection report.
    Automatically generates maintenance tickets for failed items.
    """
    try:
        insp_type = InspectionType(payload.inspection_type.upper())
    except ValueError:
        insp_type = InspectionType.PRE_TRIP

    failed_items = [item for item in payload.items if not item.passed]
    overall_status = (
        InspectionStatus.FAIL if failed_items
        else InspectionStatus.PASS
    )

    items_dict = [item.model_dump() for item in payload.items]

    inspection = VehicleInspection(
        driver_id=payload.driver_id,
        vehicle_id=payload.vehicle_id,
        company_id=payload.company_id,
        inspection_type=insp_type,
        overall_status=overall_status,
        items=items_dict,
        notes=payload.notes,
    )

    db.add(inspection)
    await db.flush()

    # Automatically generate maintenance ticket for failed inspection items
    if failed_items:
        failed_names = ", ".join([item.name for item in failed_items])
        ticket = Ticket(
            description=f"INSPECTION FAILURE ({payload.inspection_type}): {failed_names} on Vehicle #{payload.vehicle_id}. Notes: {payload.notes or 'None'}",
            status=TicketStatus.PENDING,
            risk_level=RiskLevel.HIGH,
            vehicle_id=payload.vehicle_id,
            driver_id=payload.driver_id,
        )
        db.add(ticket)
        logger.info(f"Auto-generated maintenance ticket for failed inspection {inspection.id}")

    await db.commit()
    await db.refresh(inspection)

    return InspectionResponse(
        id=inspection.id,
        driver_id=inspection.driver_id,
        vehicle_id=inspection.vehicle_id,
        company_id=inspection.company_id,
        inspection_type=inspection.inspection_type.value,
        overall_status=inspection.overall_status.value,
        items=inspection.items if isinstance(inspection.items, list) else [],
        notes=inspection.notes,
        created_at=inspection.created_at,
    )


@router.get("/inspections", response_model=List[InspectionResponse])
async def list_inspections(
    driver_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List inspection reports for a driver."""
    result = await db.execute(
        select(VehicleInspection)
        .where(VehicleInspection.driver_id == driver_id)
        .order_by(desc(VehicleInspection.created_at))
        .limit(limit)
    )
    inspections = result.scalars().all()

    return [
        InspectionResponse(
            id=insp.id,
            driver_id=insp.driver_id,
            vehicle_id=insp.vehicle_id,
            company_id=insp.company_id,
            inspection_type=insp.inspection_type.value,
            overall_status=insp.overall_status.value,
            items=insp.items if isinstance(insp.items, list) else [],
            notes=insp.notes,
            created_at=insp.created_at,
        )
        for insp in inspections
    ]
