"""
Fuel Operations Domain - API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from domain.fuel.schemas import FuelBalanceResponse, FuelHistoryResponse
from domain.fuel.queries import FuelQueryService
from domain.fuel.repository import InMemoryFuelRepository

router = APIRouter(prefix="/fuel", tags=["Fuel"])

# In a real DI container, this would be injected
_fuel_repo = InMemoryFuelRepository()
_fuel_query_service = FuelQueryService(_fuel_repo)

@router.get("/{vehicle_id}/balance", response_model=FuelBalanceResponse)
async def get_fuel_balance(vehicle_id: str):
    """
    Get the current mathematically derived fuel balance for a vehicle.
    """
    summary = _fuel_query_service.get_current_balance(vehicle_id)
    return FuelBalanceResponse(
        vehicle_id=summary.vehicle_id,
        current_balance_liters=summary.current_balance_liters,
        max_capacity_liters=summary.max_capacity_liters
    )

@router.get("/{vehicle_id}/history")
async def get_fuel_history(vehicle_id: str):
    """
    Get the immutable transaction history for a vehicle's fuel ledger.
    """
    history = _fuel_query_service.get_transaction_history(vehicle_id)
    return {
        "data": [h.model_dump() for h in history],
        "meta": {"total": len(history)}
    }
