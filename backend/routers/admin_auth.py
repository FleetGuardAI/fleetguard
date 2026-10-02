from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from database import get_db
from schemas.admin_domain import AdminLogin, Token, AdminUserResponse
from services.admin_auth_service import authenticate_admin, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_admin
from models.admin_domain import AdminUser

router = APIRouter(prefix="/api/v1/admin/auth", tags=["Admin Auth"])

@router.post("/login", summary="Admin Login")
async def login(
    payload: AdminLogin,
    db: AsyncSession = Depends(get_db)
):
    import logging
    import traceback
    logger = logging.getLogger("fleetguard")
    try:
        logger.info(f"Admin login attempt: {payload.email}")
        admin = await authenticate_admin(payload.email, payload.password, db)
        logger.info(f"Admin authenticated: {admin.id}, role_id={admin.role_id}")
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        role_value = "UNKNOWN"
        if admin.role is None:
            logger.error("admin.role is None!")
        else:
            role_value = getattr(admin.role.name, 'value', str(admin.role.name))
            
        logger.info(f"Creating token with role: {role_value}")
        access_token = create_access_token(
            data={"admin_id": str(admin.id), "role": role_value},
            expires_delta=access_token_expires
        )
        logger.info("Token created successfully")
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        logger.error(f"Error in admin login: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={"msg": str(e), "traceback": traceback.format_exc()})

@router.get("/me", response_model=AdminUserResponse, summary="Get Current Admin")
async def get_me(current_admin: AdminUser = Depends(get_current_admin)):
    return current_admin
