from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

class AdminRoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class AdminRoleResponse(AdminRoleBase):
    id: int
    class Config:
        from_attributes = True

class AdminUserBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    role_id: int
    is_active: bool = True

class AdminUserCreate(AdminUserBase):
    password: str

class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None

class AdminUserResponse(AdminUserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None
    role: Optional[AdminRoleResponse] = None
    class Config:
        from_attributes = True

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class PermissionResponse(PermissionBase):
    id: int
    class Config:
        orm_mode = True
