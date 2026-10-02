import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import async_session_factory
from services.admin_auth_service import authenticate_admin
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

async def test_login():
    async with async_session_factory() as db:
        try:
            admin = await authenticate_admin("rudra@vahan.in", "Rudra@7877", db)
            print("Login successful! User ID:", admin.id)
            print("Role name:", admin.role.name)
        except HTTPException as e:
            print("HTTP Exception:", e.status_code, e.detail)
            
            # Let's inspect the user directly
            from models.admin_domain import AdminUser
            from sqlalchemy import select
            res = await db.execute(select(AdminUser).where(AdminUser.email == "rudra@vahan.in"))
            user = res.scalar_one_or_none()
            if not user:
                print("User not found in DB at all!")
            else:
                print("User exists. Is active:", user.is_active)
                
                from services.admin_auth_service import verify_password, get_password_hash
                is_valid = verify_password("Rudra@7877", user.password_hash)
                print("Does 'Rudra@7877' verify against stored hash?", is_valid)
                print("Stored hash:", user.password_hash)
                
                # Try trimming?
                is_valid2 = verify_password("Rudra@7877".strip(), user.password_hash)
                print("Does stripped password verify?", is_valid2)
                print("New hash of password:", get_password_hash("Rudra@7877"))
        except Exception as e:
            print("Other error:", e)

if __name__ == "__main__":
    asyncio.run(test_login())
