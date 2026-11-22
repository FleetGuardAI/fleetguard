import os
import sys
import logging
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
from config import settings
from database import get_db

logger = logging.getLogger("fleetguard.admin_auth")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12 # 12 hours
_TEST_ADMIN_SECRET = "test-only-admin-jwt-secret-not-for-production-min32chars"


def get_admin_jwt_secret() -> str:
    """
    FG-SEC-003: Require a dedicated, strong admin JWT secret.
    Rejects fallback to default or shared user secrets.
    Enforces minimum 32-character key length.
    """
    secret = getattr(settings, "ADMIN_JWT_SECRET", None) or os.getenv("ADMIN_JWT_SECRET")
    if secret and str(secret).strip():
        secret_str = str(secret).strip()
        if len(secret_str) < 32:
            raise RuntimeError(
                "ADMIN_JWT_SECRET must be at least 32 characters long for production security."
            )
        return secret_str

    # In test environments, provide an isolated test secret if none was explicitly configured
    is_test_env = (
        "pytest" in sys.modules
        or bool(os.getenv("PYTEST_CURRENT_TEST"))
        or bool(os.getenv("TEST_DATABASE_URL"))
    )
    if is_test_env:
        return _TEST_ADMIN_SECRET

    raise RuntimeError(
        "CRITICAL: ADMIN_JWT_SECRET environment variable is missing or empty. "
        "Production deployment requires a dedicated, cryptographically secure 32+ character admin JWT secret."
    )


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
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "token_type": "admin_access"})
    encoded_jwt = jwt.encode(to_encode, get_admin_jwt_secret(), algorithm=ALGORITHM)
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
        payload = jwt.decode(token, get_admin_jwt_secret(), algorithms=[ALGORITHM])
        if payload.get("token_type") != "admin_access":
            logger.warning("Rejected non-admin token type presented to admin endpoint")
            raise credentials_exception
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
        role_name = getattr(admin.role.name, "value", str(admin.role.name)) if (admin.role and getattr(admin.role, 'name', None)) else ""
        if role_name == "SUPER_ADMIN" or (admin.role and getattr(admin.role, 'name', None) == "SUPER_ADMIN"):
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
