"""
FleetGuard — Fuel Domain API Router
Provides Read-Only REST APIs for the Fuel Business Domain.
(Write operations are processed asynchronously via Operational Events).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from database import get_db
from models.vehicle_domain import Vehicle
from repositories.fuel_repository import FuelRepository
from schemas.fuel_domain import FuelTransactionResponse, FuelStateResponse, FuelHistoryResponse

router = APIRouter(prefix="/v1", tags=["Fuel Domain"])


@router.get("/fuel/{transaction_id}", response_model=FuelTransactionResponse)
async def get_fuel_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db)
) -> FuelTransactionResponse:
    """Get a specific fuel transaction by ID."""
    repo = FuelRepository(db)
    tx = await repo.get_transaction_by_id(transaction_id)
    if not tx:
        raise HTTPException(404, f"Fuel transaction {transaction_id} not found")
    return FuelTransactionResponse.model_validate(tx)


@router.get("/vehicles/{vehicle_id}/fuel", response_model=FuelStateResponse)
async def get_vehicle_fuel_state(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db)
) -> FuelStateResponse:
    """Get the current known fuel state for a vehicle."""
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")
        
    repo = FuelRepository(db)
    state = await repo.get_fuel_state_by_truck(vehicle_id)
    
    if not state:
        raise HTTPException(404, f"No fuel state known for vehicle {vehicle_id}")
        
    return FuelStateResponse.model_validate(state)


@router.get("/vehicles/{vehicle_id}/fuel/history", response_model=FuelHistoryResponse)
async def get_vehicle_fuel_history(
    vehicle_id: int,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> FuelHistoryResponse:
    """Get the fuel transaction history for a vehicle."""
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")
        
    repo = FuelRepository(db)
    transactions = await repo.get_fuel_transactions_by_truck(vehicle_id, limit=limit)
    
    history_responses = [FuelTransactionResponse.model_validate(tx) for tx in transactions]
    
    return FuelHistoryResponse(
        truck_id=vehicle_id,
        history=history_responses
    )
