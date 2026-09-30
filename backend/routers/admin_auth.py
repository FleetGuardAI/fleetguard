from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from database import get_db
from schemas.admin_domain import AdminLogin, Token, AdminUserResponse
from services.admin_auth_service import authenticate_admin, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_admin
from models.admin_domain import AdminUser

router = APIRouter(prefix="/api/v1/admin/auth", tags=["Admin Auth"])

@router.post("/login", response_model=Token, summary="Admin Login")
async def login(
    payload: AdminLogin,
    db: AsyncSession = Depends(get_db)
):
    admin = await authenticate_admin(payload.email, payload.password, db)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"admin_id": str(admin.id), "role": admin.role.name},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=AdminUserResponse, summary="Get Current Admin")
async def get_me(current_admin: AdminUser = Depends(get_current_admin)):
    return current_admin
