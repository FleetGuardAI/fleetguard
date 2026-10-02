import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from models.admin_domain import AdminUser, AdminRole, Permission, AdminRolePermission
from schemas.admin_domain import AdminLogin, Token
from database import get_db

SECRET_KEY = os.getenv("ADMIN_JWT_SECRET", "super-secret-admin-key-do-not-use-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12 # 12 hours

from utils.security import verify_password as utils_verify_password, hash_password
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/admin/auth/login")

def verify_password(plain_password, hashed_password):
    return utils_verify_password(plain_password, hashed_password)

def get_password_hash(password):
    return hash_password(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def authenticate_admin(email: str, password: str, db: AsyncSession) -> AdminUser:
    result = await db.execute(select(AdminUser).where(AdminUser.email == email))
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin account is inactive")
    if not verify_password(password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    # Update last login
    admin.last_login = datetime.utcnow()
    await db.commit()
    
    return admin

async def get_current_admin(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> AdminUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id: str = payload.get("admin_id")
        if admin_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    result = await db.execute(select(AdminUser).where(AdminUser.id == int(admin_id)))
    admin = result.scalar_one_or_none()
    if admin is None:
        raise credentials_exception
    if not admin.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin account is inactive")
    return admin

def require_admin_permission(permission_name: str):
    async def permission_checker(admin: AdminUser = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
        from models.admin_domain import AdminRole, Permission, AdminRolePermission
        from sqlalchemy import select
        
        # Super admin has all permissions
        if admin.role.name == "SUPER_ADMIN":
            return admin
            
        result = await db.execute(
            select(Permission.name)
            .join(AdminRolePermission, AdminRolePermission.permission_id == Permission.id)
            .where(AdminRolePermission.role_id == admin.role_id)
        )
        permissions = result.scalars().all()
        
        if permission_name not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Missing required permission: {permission_name}"
            )
        return admin
    return permission_checker

async def create_audit_log(
    db: AsyncSession, 
    admin_id: int, 
    action: str, 
    resource_type: Optional[str] = None, 
    resource_id: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    reason: Optional[str] = None
):
    from models.admin_domain import AdminAuditLog
    log = AdminAuditLog(
        admin_id=admin_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_value,
        new_value=new_value,
        reason=reason
    )
    db.add(log)
    await db.commit()
