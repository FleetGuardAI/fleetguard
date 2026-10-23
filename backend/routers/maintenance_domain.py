"""
FleetGuard — Maintenance Domain API Router
Provides Read-Only REST APIs for the Maintenance Business Domain.
(Write operations are processed asynchronously via Operational Events).

Security: All endpoints require authentication and are scoped to the
authenticated user's company. Maintenance records are linked to company
via the Vehicle→company_id relationship.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database import get_db, get_read_uow
from infrastructure.uow import AbstractUnitOfWork
from models.maintenance_domain import MaintenanceRecord, MaintenanceStatus, MaintenanceCategory
from models.vehicle_domain import Vehicle
from schemas.maintenance_domain import MaintenanceRecordResponse, MaintenanceCreateRequest, MaintenanceUpdateRequest
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from datetime import datetime, timezone
import uuid
from services.auth_service import get_current_user
from models.user import User
from services.odometer_service import OdometerService

router = APIRouter(prefix="/v1", tags=["Maintenance Domain"])


@router.get("/maintenance", response_model=List[MaintenanceRecordResponse])
async def list_maintenance(
    status: Optional[MaintenanceStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MaintenanceRecordResponse]:
    """List all maintenance records with optional status filter. Company-scoped."""
    company_id = current_user.company_id

    query = (
        select(MaintenanceRecord)
        .outerjoin(Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id)
        .where(Vehicle.company_id == company_id)
    )
    if status:
        query = query.where(MaintenanceRecord.status == status)
    query = query.order_by(MaintenanceRecord.id.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    records = result.scalars().all()
    return [MaintenanceRecordResponse.model_validate(r) for r in records]


@router.get("/maintenance/search", response_model=List[MaintenanceRecordResponse])
async def search_maintenance(
    status: Optional[MaintenanceStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MaintenanceRecordResponse]:
    """Search for maintenance records based on criteria. Company-scoped."""
    company_id = current_user.company_id

    query = (
        select(MaintenanceRecord)
        .outerjoin(Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id)
        .where(Vehicle.company_id == company_id)
    )
    if status:
        query = query.where(MaintenanceRecord.status == status)
    query = query.order_by(MaintenanceRecord.id.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    records = result.scalars().all()
    return [MaintenanceRecordResponse.model_validate(r) for r in records]


@router.get("/maintenance/{maintenance_id}", response_model=MaintenanceRecordResponse)
async def get_maintenance(
    maintenance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaintenanceRecordResponse:
    """Get a single maintenance record by ID. Verifies company ownership."""
    company_id = current_user.company_id

    result = await db.execute(
        select(MaintenanceRecord)
        .outerjoin(Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id)
        .where(MaintenanceRecord.id == maintenance_id, Vehicle.company_id == company_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(404, f"Maintenance Record {maintenance_id} not found")
    return MaintenanceRecordResponse.model_validate(record)


@router.get("/vehicles/{vehicle_id}/maintenance", response_model=List[MaintenanceRecordResponse])
async def get_maintenance_by_vehicle(
    vehicle_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MaintenanceRecordResponse]:
    """Get all maintenance records associated with a specific vehicle. Verifies vehicle ownership."""
    company_id = current_user.company_id

    # Verify vehicle belongs to the company
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.company_id != company_id:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")

    result = await db.execute(
        select(MaintenanceRecord)
        .where(MaintenanceRecord.vehicle_id == vehicle_id)
        .order_by(MaintenanceRecord.id.desc())
        .offset(offset)
        .limit(limit)
    )
    records = result.scalars().all()
    return [MaintenanceRecordResponse.model_validate(r) for r in records]


@router.post("/maintenance", response_model=MaintenanceRecordResponse, status_code=201)
async def create_maintenance(
    payload: MaintenanceCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaintenanceRecordResponse:
    company_id = current_user.company_id
    
    # Verify vehicle
    if payload.vehicle_id:
        vehicle = await db.get(Vehicle, payload.vehicle_id)
        if not vehicle or vehicle.company_id != company_id:
            raise HTTPException(403, "Unauthorized vehicle")

    # Create Expense if COMPLETED and cost exists
    expense_id = None
    if payload.status == MaintenanceStatus.COMPLETED and payload.cost and payload.cost > 0:
        expense = Expense(
            company_id=company_id,
            vehicle_id=payload.vehicle_id,
            driver_id=payload.driver_id,
            trip_id=payload.trip_id,
            amount=payload.cost,
            category=ExpenseCategory.MAINTENANCE,
            status=ExpenseStatus.PENDING,
            expense_date=payload.completed_date or datetime.now(timezone.utc),
            description=payload.description or "Vehicle Maintenance"
        )
        db.add(expense)
        await db.flush()
        expense_id = expense.id

    # Update historical/last service odometer for completion
    if payload.status == MaintenanceStatus.COMPLETED and payload.vehicle_id:
        vehicle = await db.get(Vehicle, payload.vehicle_id)
        if vehicle:
            vehicle.last_service_date = payload.completed_date or datetime.now(timezone.utc)
            if payload.odometer is not None:
                vehicle.last_service_odometer = payload.odometer
                # Update current odometer ONLY if it moves forward
                OdometerService.update_odometer_if_valid(vehicle, payload.odometer, payload.completed_date or datetime.now(timezone.utc))
            vehicle.maintenance_status = "NOT_DUE"
            db.add(vehicle)

    record = MaintenanceRecord(
        business_id=f"MNT-{uuid.uuid4().hex[:6].upper()}",
        company_id=company_id,
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
        trip_id=payload.trip_id,
        category=payload.category,
        status=payload.status,
        scheduled_date=payload.scheduled_date,
        completed_date=payload.completed_date,
        workshop=payload.workshop,
        description=payload.description,
        odometer=payload.odometer,
        cost=payload.cost,
        expense_id=expense_id
    )
    db.add(record)
    await db.flush()
    await ensure_maintenance_expense(db, record)
    await db.commit()
    await db.refresh(record)
    return MaintenanceRecordResponse.model_validate(record)

@router.patch("/maintenance/{maintenance_id}", response_model=MaintenanceRecordResponse)
async def update_maintenance(
    maintenance_id: int,
    payload: MaintenanceUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaintenanceRecordResponse:
    company_id = current_user.company_id
    
    result = await db.execute(
        select(MaintenanceRecord).where(MaintenanceRecord.id == maintenance_id, MaintenanceRecord.company_id == company_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(404, "Maintenance record not found")
        
    # Apply updates
    if payload.status:
        record.status = payload.status
    if payload.completed_date:
        record.completed_date = payload.completed_date
    if payload.cost is not None:
        record.cost = payload.cost
    if payload.odometer is not None:
        record.odometer = payload.odometer
    if payload.description is not None:
        record.description = payload.description
    if payload.workshop is not None:
        record.workshop = payload.workshop
    if payload.other_cost is not None:
        record.other_cost = payload.other_cost
    if payload.trip_id is not None:
        record.trip_id = payload.trip_id
    if payload.driver_id is not None:
        record.driver_id = payload.driver_id

    # Create Expense if transitioned to COMPLETED and cost > 0
    if record.status == MaintenanceStatus.COMPLETED and record.cost and record.cost > 0 and not record.expense_id:
        expense = Expense(
            company_id=company_id,
            vehicle_id=record.vehicle_id,
            driver_id=record.driver_id,
            trip_id=record.trip_id,
            amount=record.cost,
            category=ExpenseCategory.MAINTENANCE,
            status=ExpenseStatus.PENDING,
            expense_date=record.completed_date or datetime.now(timezone.utc),
            description=record.description or "Vehicle Maintenance"
        )
        db.add(expense)
        await db.flush()
        record.expense_id = expense.id
        
    # Reset Vehicle Maintenance Status if transitioned to COMPLETED
    if record.status == MaintenanceStatus.COMPLETED and record.vehicle_id:
        vehicle = await db.get(Vehicle, record.vehicle_id)
        if vehicle:
            vehicle.last_service_date = record.completed_date or datetime.now(timezone.utc)
            if record.odometer is not None:
                vehicle.last_service_odometer = record.odometer
                # Update current odometer ONLY if it moves forward
                OdometerService.update_odometer_if_valid(vehicle, record.odometer, record.completed_date or datetime.now(timezone.utc))
            vehicle.maintenance_status = "NOT_DUE"
            db.add(vehicle)
        
    await db.commit()
    await db.refresh(record)
    return MaintenanceRecordResponse.model_validate(record)


from typing import Optional
from datetime import datetime
from sqlalchemy import or_

@router.get("/maintenance/analytics")
async def get_maintenance_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company_id = current_user.company_id
    
    date_filters = [MaintenanceRecord.company_id == company_id, MaintenanceRecord.status == MaintenanceStatus.COMPLETED]
    if start_date:
        date_filters.append(MaintenanceRecord.completed_date >= start_date)
    if end_date:
        date_filters.append(MaintenanceRecord.completed_date <= end_date)
    
    # 1. Spend & Event Counts
    from sqlalchemy import func
    
    agg_query = select(
        func.sum(MaintenanceRecord.cost).label('total_spend'),
        func.sum(MaintenanceRecord.cost).filter(MaintenanceRecord.category == MaintenanceCategory.PREVENTIVE).label('preventive_spend'),
        func.sum(MaintenanceRecord.cost).filter(MaintenanceRecord.category != MaintenanceCategory.PREVENTIVE).label('corrective_spend'),
        func.count(MaintenanceRecord.id).label('completed_count')
    ).where(*date_filters)
    
    agg_result = await db.execute(agg_query)
    agg_row = agg_result.one()
    
    total_spend = agg_row.total_spend or 0.0
    preventive_spend = agg_row.preventive_spend or 0.0
    corrective_spend = agg_row.corrective_spend or 0.0
    completed_count = agg_row.completed_count or 0
    
    # Spend by vehicle
    veh_query = select(
        MaintenanceRecord.vehicle_id,
        func.sum(MaintenanceRecord.cost).label('vehicle_spend')
    ).where(*date_filters).group_by(MaintenanceRecord.vehicle_id)
    veh_result = await db.execute(veh_query)
    spend_by_vehicle = {row.vehicle_id: row.vehicle_spend for row in veh_result.all() if row.vehicle_id}
    
    # Cost per km by vehicle (simplified for now, ideally joins with Trip/GPS data)
    cost_per_km_by_vehicle = {}
    # Could be populated by fetching vehicle distance in the same date range, but leaving empty dict for now to prevent NameError
    
    # Total events (including non-completed)
    total_events_query = select(func.count(MaintenanceRecord.id)).where(MaintenanceRecord.company_id == company_id)
    if start_date:
        total_events_query = total_events_query.where(MaintenanceRecord.scheduled_date >= start_date)
    if end_date:
        total_events_query = total_events_query.where(MaintenanceRecord.scheduled_date <= end_date)
    total_events = await db.scalar(total_events_query) or 0
    
    # 2. Overdue Vehicles
    vehicle_query = select(func.count(Vehicle.id)).where(Vehicle.company_id == company_id, Vehicle.maintenance_status == "OVERDUE")
    overdue_count = await db.scalar(vehicle_query) or 0
    
    return {
        "total_spend": total_spend,
        "preventive_spend": preventive_spend,
        "corrective_spend": corrective_spend,
        "completed_count": completed_count,
        "overdue_count": overdue_count,
        "spend_by_vehicle": spend_by_vehicle,
        "cost_per_km_by_vehicle": cost_per_km_by_vehicle,
        "total_events": total_events
    }

from models.maintenance_domain import MaintenancePart, MaintenanceLabour, MaintenanceDocument
from models.expense_domain import ExpenseStatus
from schemas.maintenance_domain import (
    MaintenancePartCreate, MaintenancePartUpdate, MaintenancePartResponse,
    MaintenanceLabourCreate, MaintenanceLabourUpdate, MaintenanceLabourResponse,
    MaintenanceDocumentCreate, MaintenanceDocumentResponse
)

from services.maintenance_finance import ensure_maintenance_expense

async def _recalculate_maintenance_cost(db: AsyncSession, record: MaintenanceRecord):
    parts_total = sum(p.total_cost for p in record.parts)
    labour_total = sum(l.total_cost for l in record.labour)
    record.cost = parts_total + labour_total + record.other_cost
    
    # Delegate all expense recognition safely
    await ensure_maintenance_expense(db, record)

async def _verify_mutability(db: AsyncSession, record: MaintenanceRecord):
    if record.status == MaintenanceStatus.COMPLETED and record.expense_id:
        expense = await db.get(Expense, record.expense_id)
        if expense and expense.status == ExpenseStatus.APPROVED:
            raise HTTPException(400, "Maintenance is finalized and expense is approved. Parts and labour cannot be modified.")

# ----------------- PARTS -----------------

@router.post("/maintenance/{id}/parts", response_model=MaintenancePartResponse, status_code=201)
async def add_maintenance_part(
    id: int,
    payload: MaintenancePartCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = await db.get(MaintenanceRecord, id)
    if not record or record.company_id != current_user.company_id:
        raise HTTPException(404, "Maintenance record not found")
        
    await _verify_mutability(db, record)
    
    if payload.quantity <= 0 or payload.unit_cost < 0:
        raise HTTPException(400, "Quantity must be > 0 and unit_cost must be >= 0")
        
    total = payload.quantity * payload.unit_cost
    
    part = MaintenancePart(
        maintenance_record_id=id,
        name=payload.name,
        part_number=payload.part_number,
        quantity=payload.quantity,
        unit_cost=payload.unit_cost,
        total_cost=total
    )
    db.add(part)
    record.parts.append(part)
    
    await _recalculate_maintenance_cost(db, record)
    await db.commit()
    await db.refresh(part)
    return part

@router.patch("/maintenance/{id}/parts/{part_id}", response_model=MaintenancePartResponse)
async def update_maintenance_part(
    id: int,
    part_id: int,
    payload: MaintenancePartUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = await db.get(MaintenanceRecord, id)
    if not record or record.company_id != current_user.company_id:
        raise HTTPException(404, "Maintenance record not found")
        
    await _verify_mutability(db, record)
    
    part = await db.get(MaintenancePart, part_id)
    if not part or part.maintenance_record_id != id:
        raise HTTPException(404, "Part not found")
        
    if payload.name is not None:
        part.name = payload.name
    if payload.part_number is not None:
        part.part_number = payload.part_number
    if payload.quantity is not None:
        if payload.quantity <= 0:
            raise HTTPException(400, "Quantity must be > 0")
        part.quantity = payload.quantity
    if payload.unit_cost is not None:
        if payload.unit_cost < 0:
            raise HTTPException(400, "unit_cost must be >= 0")
        part.unit_cost = payload.unit_cost
        
    part.total_cost = part.quantity * part.unit_cost
    
    await _recalculate_maintenance_cost(db, record)
    await db.commit()
    await db.refresh(part)
    return part

@router.delete("/maintenance/{id}/parts/{part_id}", status_code=204)
async def delete_maintenance_part(
    id: int,
    part_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = await db.get(MaintenanceRecord, id)
    if not record or record.company_id != current_user.company_id:
        raise HTTPException(404, "Maintenance record not found")
        
    await _verify_mutability(db, record)
    
    part = await db.get(MaintenancePart, part_id)
    if not part or part.maintenance_record_id != id:
        raise HTTPException(404, "Part not found")
        
    await db.delete(part)
    record.parts.remove(part)
    
    await _recalculate_maintenance_cost(db, record)
    await db.commit()

# ----------------- LABOUR -----------------

@router.post("/maintenance/{id}/labour", response_model=MaintenanceLabourResponse, status_code=201)
async def add_maintenance_labour(
    id: int,
    payload: MaintenanceLabourCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = await db.get(MaintenanceRecord, id)
    if not record or record.company_id != current_user.company_id:
        raise HTTPException(404, "Maintenance record not found")
        
    await _verify_mutability(db, record)
    
    if payload.hours <= 0 or payload.hourly_rate < 0:
        raise HTTPException(400, "Hours must be > 0 and hourly_rate must be >= 0")
        
    total = payload.hours * payload.hourly_rate
    
    labour = MaintenanceLabour(
        maintenance_record_id=id,
        description=payload.description,
        hours=payload.hours,
        hourly_rate=payload.hourly_rate,
        total_cost=total
    )
    db.add(labour)
    record.labour.append(labour)
    
    await _recalculate_maintenance_cost(db, record)
    await db.commit()
    await db.refresh(labour)
    return labour

@router.patch("/maintenance/{id}/labour/{labour_id}", response_model=MaintenanceLabourResponse)
async def update_maintenance_labour(
    id: int,
    labour_id: int,
    payload: MaintenanceLabourUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = await db.get(MaintenanceRecord, id)
    if not record or record.company_id != current_user.company_id:
        raise HTTPException(404, "Maintenance record not found")
        
    await _verify_mutability(db, record)
    
    labour = await db.get(MaintenanceLabour, labour_id)
    if not labour or labour.maintenance_record_id != id:
        raise HTTPException(404, "Labour not found")
        
    if payload.description is not None:
        labour.description = payload.description
    if payload.hours is not None:
        if payload.hours <= 0:
            raise HTTPException(400, "Hours must be > 0")
        labour.hours = payload.hours
    if payload.hourly_rate is not None:
        if payload.hourly_rate < 0:
            raise HTTPException(400, "hourly_rate must be >= 0")
        labour.hourly_rate = payload.hourly_rate
        
    labour.total_cost = labour.hours * labour.hourly_rate
    
    await _recalculate_maintenance_cost(db, record)
    await db.commit()
    await db.refresh(labour)
    return labour

@router.delete("/maintenance/{id}/labour/{labour_id}", status_code=204)
async def delete_maintenance_labour(
    id: int,
    labour_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = await db.get(MaintenanceRecord, id)
    if not record or record.company_id != current_user.company_id:
        raise HTTPException(404, "Maintenance record not found")
        
    await _verify_mutability(db, record)
    
    labour = await db.get(MaintenanceLabour, labour_id)
    if not labour or labour.maintenance_record_id != id:
        raise HTTPException(404, "Labour not found")
        
    await db.delete(labour)
    record.labour.remove(labour)
    
    await _recalculate_maintenance_cost(db, record)
    await db.commit()

# ----------------- DOCUMENTS -----------------

@router.post("/maintenance/{id}/documents", response_model=MaintenanceDocumentResponse, status_code=201)
async def add_maintenance_document(
    id: int,
    payload: MaintenanceDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = await db.get(MaintenanceRecord, id)
    if not record or record.company_id != current_user.company_id:
        raise HTTPException(404, "Maintenance record not found")
        
    from models.document import Document
    doc = await db.get(Document, payload.document_id)
    if not doc or doc.company_id != current_user.company_id:
        raise HTTPException(403, "Document access denied")
        
    from sqlalchemy.exc import IntegrityError
    maint_doc = MaintenanceDocument(
        maintenance_record_id=id,
        document_id=payload.document_id
    )
    db.add(maint_doc)
    try:
        await db.commit()
        await db.refresh(maint_doc)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(409, "Document is already linked to this maintenance record")
    return maint_doc

@router.get("/maintenance/{id}/documents", response_model=list[MaintenanceDocumentResponse])
async def get_maintenance_documents(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = await db.get(MaintenanceRecord, id)
    if not record or record.company_id != current_user.company_id:
        raise HTTPException(404, "Maintenance record not found")
        
    query = select(MaintenanceDocument).where(MaintenanceDocument.maintenance_record_id == id)
    res = await db.execute(query)
    docs = res.scalars().all()
    return docs

@router.delete("/maintenance/{id}/documents/{document_id}", status_code=204)
async def delete_maintenance_document(
    id: int,
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    record = await db.get(MaintenanceRecord, id)
    if not record or record.company_id != current_user.company_id:
        raise HTTPException(404, "Maintenance record not found")
        
    import uuid
    doc_uuid = uuid.UUID(document_id)
    
    query = select(MaintenanceDocument).where(
        MaintenanceDocument.maintenance_record_id == id,
        MaintenanceDocument.document_id == doc_uuid
    )
    res = await db.execute(query)
    maint_doc = res.scalars().first()
    
    if not maint_doc:
        raise HTTPException(404, "Document linkage not found")
        
    await db.delete(maint_doc)
    await db.commit()
