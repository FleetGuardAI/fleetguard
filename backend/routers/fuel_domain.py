"""
FleetGuard — Fuel Domain API Router
Provides Read-Only REST APIs for the Fuel Business Domain.
(Write operations are processed asynchronously via Operational Events).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Union
from jose import jwt, JWTError

from database import get_db
from models.vehicle_domain import Vehicle
from repositories.fuel_repository import FuelRepository
from schemas.fuel_domain import FuelTransactionResponse, FuelStateResponse, FuelHistoryResponse
from services.auth_service import get_current_user
from services.admin_auth_service import get_current_admin, get_admin_jwt_secret
from models.user import User, UserRole
from models.admin_domain import AdminUser

router = APIRouter(prefix="/v1", tags=["Fuel Domain"])

security_bearer = HTTPBearer(auto_error=False)


async def get_fuel_caller(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncSession = Depends(get_db),
) -> Union[AdminUser, User]:
    """
    FG-SEC-004 / Batch 1.3: Super Admin Authentication Separation.
    Distinguishes dedicated platform AdminUser from ordinary company User.
    - If Bearer token is signed by ADMIN_JWT_SECRET with token_type='admin_access',
      authenticates as platform AdminUser.
    - Otherwise, falls back to standard tenant User authentication via get_current_user.
    - A normal User JWT can NEVER manufacture or claim platform AdminUser identity.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # 1. Check for dedicated Admin token signed by ADMIN_JWT_SECRET
    try:
        admin_secret = get_admin_jwt_secret()
        payload = jwt.decode(token, admin_secret, algorithms=["HS256"])
        if payload.get("token_type") == "admin_access" and payload.get("admin_id") is not None:
            admin_id = int(payload.get("admin_id"))
            result = await db.execute(select(AdminUser).where(AdminUser.id == admin_id))
            admin = result.scalar_one_or_none()
            if admin and admin.is_active:
                return admin
    except Exception:
        pass  # Not an admin token; proceed to user verification

    # 2. Standard tenant User authentication (verified against SECRET_KEY and auth_sessions)
    user = await get_current_user(token=token, db=db)
    return user


@router.get("/fuel/{transaction_id}", response_model=FuelTransactionResponse)
async def get_fuel_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
    caller: Union[AdminUser, User] = Depends(get_fuel_caller),
) -> FuelTransactionResponse:
    """
    Get a specific fuel transaction by ID.
    Enforces strict tenant scoping for all company users.
    Platform AdminUsers (verified by ADMIN_JWT_SECRET) are permitted unscoped access.
    """
    repo = FuelRepository(db)
    if isinstance(caller, AdminUser):
        # Platform Administrator: Unscoped access permitted for support / ops
        tx = await repo.get_transaction_by_id_unscoped(transaction_id)
    else:
        # Ordinary company user: Strictly scoped to company_id (regardless of User.role)
        if not caller.company_id:
            raise HTTPException(403, "User has no assigned company")
        tx = await repo.get_transaction_by_id(transaction_id, company_id=caller.company_id)

    if not tx:
        raise HTTPException(404, f"Fuel transaction {transaction_id} not found")
    return FuelTransactionResponse.model_validate(tx)


@router.get("/admin/fuel/{transaction_id}", response_model=FuelTransactionResponse, tags=["Admin Fuel"])
async def get_admin_fuel_transaction(
    transaction_id: int,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> FuelTransactionResponse:
    """
    Dedicated Platform Administrator Fuel Lookup.
    Requires AdminUser authentication via ADMIN_JWT_SECRET.
    Ordinary company users cannot access this endpoint.
    """
    repo = FuelRepository(db)
    tx = await repo.get_transaction_by_id_unscoped(transaction_id)
    if not tx:
        raise HTTPException(404, f"Fuel transaction {transaction_id} not found")
    return FuelTransactionResponse.model_validate(tx)


@router.get("/vehicles/{vehicle_id}/fuel", response_model=FuelStateResponse)
async def get_vehicle_fuel_state(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FuelStateResponse:
    """Get the current known fuel state for a vehicle."""
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.company_id != current_user.company_id:
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FuelHistoryResponse:
    """Get the fuel transaction history for a vehicle."""
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.company_id != current_user.company_id:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")

    repo = FuelRepository(db)
    transactions = await repo.get_fuel_transactions_by_truck(
        vehicle_id, company_id=current_user.company_id, limit=limit
    )

    history_responses = [FuelTransactionResponse.model_validate(tx) for tx in transactions]

    return FuelHistoryResponse(
        truck_id=vehicle_id,
        history=history_responses
    )
