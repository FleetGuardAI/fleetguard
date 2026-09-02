"""
FleetGuard — Vehicle Domain API Router
Provides REST APIs for Vehicle Business Domain CRUD operations.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, get_read_uow
from infrastructure.uow import AbstractUnitOfWork
from services.vehicle_service import VehicleService
from models.vehicle_domain import Vehicle, VehicleStatus
from models.operational_event import OperationalEvent, EventType, EntityType, CaptureMethod
from models.user import User
from schemas.vehicle_domain import VehicleResponse, VehicleCreate, VehicleUpdated
from services.auth_service import get_current_user

router = APIRouter(prefix="/v1", tags=["Vehicle Domain"])


@router.get("/vehicles", response_model=List[VehicleResponse])
async def list_vehicles(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> List[VehicleResponse]:
    """List all vehicles with optional active filter."""
    service = VehicleService(uow)
    vehicles = await service.search_vehicles(is_active=is_active, limit=limit, offset=offset, company_id=current_user.company_id)
    return [VehicleResponse.model_validate(v) for v in vehicles]


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(
    vehicle_id: int, 
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> VehicleResponse:
    """Get a single vehicle by ID."""
    service = VehicleService(uow)
    vehicle = await service.get_vehicle(vehicle_id, company_id=current_user.company_id)
    if not vehicle:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")
    return VehicleResponse.model_validate(vehicle)


@router.post("/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    payload: VehicleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VehicleResponse:
    """Register a new vehicle in the database."""
    reg_num = payload.registration_number or payload.license_plate
    if not reg_num:
        raise HTTPException(status_code=400, detail="License plate / registration number is required")

    existing = await db.execute(select(Vehicle).where(Vehicle.registration_number == reg_num))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Vehicle with plate {reg_num} is already registered")

    vehicle = Vehicle(
        registration_number=reg_num,
        make=payload.make,
        model=payload.model,
        year=payload.year,
        vin=payload.vin,
        engine_number=payload.engine_number,
        tank_capacity=payload.tank_capacity or 400.0,
        status=VehicleStatus.ACTIVE,
        origin_type="rest_api",
        company_id=current_user.company_id
    )
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)

    # Log operational event
    event = OperationalEvent(
        company_id=current_user.company_id,
        event_type=EventType.VEHICLE_REGISTERED,
        entity_type=EntityType.VEHICLE,
        entity_id=vehicle.registration_number,
        company_id=current_user.company_id,
        occurred_at=datetime.now(timezone.utc),
        capture_method=CaptureMethod.API_INTEGRATION,
        payload={"make": vehicle.make, "registration_number": vehicle.registration_number},
    )
    db.add(event)
    await db.commit()

    return VehicleResponse.model_validate(vehicle)


@router.patch("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: int,
    payload: VehicleUpdated,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VehicleResponse:
    """Update vehicle details."""
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.company_id != current_user.company_id:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")

    if payload.license_plate:
        vehicle.registration_number = payload.license_plate
    if payload.make:
        vehicle.make = payload.make
    if payload.model:
        vehicle.model = payload.model
    if payload.year is not None:
        vehicle.year = payload.year
    if payload.tank_capacity is not None:
        vehicle.tank_capacity = payload.tank_capacity
    if payload.ownership_info:
        vehicle.ownership_info = payload.ownership_info
    if payload.driver_id is not None:
        from models.driver_domain import Driver
        driver = await db.get(Driver, payload.driver_id)
        if not driver or driver.company_id != current_user.company_id:
            raise HTTPException(400, "Invalid driver_id or driver belongs to another company")
        vehicle.assigned_driver_id = payload.driver_id

    await db.commit()
    await db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)


@router.delete("/vehicles/{vehicle_id}", status_code=status.HTTP_200_OK)
async def delete_vehicle(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete/archive a vehicle."""
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.company_id != current_user.company_id:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")

    await db.delete(vehicle)
    await db.commit()
    return {"message": f"Vehicle {vehicle_id} deleted successfully"}


@router.post("/vehicles/{vehicle_id}/upload-document")
async def upload_vehicle_document(
    vehicle_id: int,
    document_type: str = Form(..., description="rc, insurance, puc, fitness_certificate, permit"),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a vehicle document (RC, Insurance, PUC, Fitness, Permit).
    Uses the unified document pipeline to upload, OCR, and store metadata/expiry.
    """
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.company_id != current_user.company_id:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")

    valid_types = ["rc", "insurance", "puc", "fitness_certificate", "permit"]
    if document_type not in valid_types:
        raise HTTPException(400, f"Invalid document type. Must be one of: {valid_types}")

    from services.unified_pipeline_service import UnifiedPipelineService
    from models.operational_event import EntityType
    
    pipeline = UnifiedPipelineService(db)
    
    try:
        url, extracted_fields = await pipeline.process_document(
            file=file,
            document_type=document_type,
            entity_type=EntityType.VEHICLE,
            entity_id=str(vehicle.id),
            uploaded_by=f"user_{current_user.id}",
            company_id=current_user.company_id
        )
    except Exception as e:
        import logging
        logger = logging.getLogger("fleetguard.vehicle_domain")
        logger.error(f"Failed to process vehicle document upload: {e}")
        raise HTTPException(500, "Failed to upload and process document")

    # Update vehicle record
    setattr(vehicle, f"{document_type}_url", url)

    await db.commit()
    await db.refresh(vehicle)

    return {
        "message": f"{document_type} uploaded successfully",
        "url": url,
        "extracted_fields": extracted_fields
    }


@router.post("/vehicles/{vehicle_id}/assign-driver", response_model=VehicleResponse)
async def assign_driver_to_vehicle(
    vehicle_id: int,
    driver_id: int = Query(..., description="Driver ID to assign to this vehicle"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VehicleResponse:
    """Explicitly assign a driver to a vehicle, with fleet isolation checks."""
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.company_id != current_user.company_id:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")
        
    from models.driver_domain import Driver
    driver = await db.get(Driver, driver_id)
    if not driver or driver.company_id != current_user.company_id:
        raise HTTPException(400, "Invalid driver or driver belongs to another fleet")

    vehicle.assigned_driver_id = driver_id
    await db.commit()
    await db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)


@router.delete("/vehicles/{vehicle_id}/unassign-driver", response_model=VehicleResponse)
async def unassign_driver_from_vehicle(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> VehicleResponse:
    """Remove driver assignment from a vehicle."""
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.company_id != current_user.company_id:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")

    vehicle.assigned_driver_id = None
    await db.commit()
    await db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)
