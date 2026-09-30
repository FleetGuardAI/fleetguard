import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import async_session_factory
from models.admin_domain import AdminUser, AdminRole, AdminRoleType
from services.admin_auth_service import get_password_hash

async def reset_admin():
    async with async_session_factory() as db:
        from sqlalchemy import select, delete
        
        # Delete old admin users
        await db.execute(delete(AdminUser))
        await db.commit()
        print("Deleted all old admin users.")
        
        # Check and Create roles
        result = await db.execute(select(AdminRole).where(AdminRole.name == AdminRoleType.SUPER_ADMIN))
        super_admin_role = result.scalars().first()
        if not super_admin_role:
            super_admin_role = AdminRole(name=AdminRoleType.SUPER_ADMIN, description="Full Access")
            admin_role = AdminRole(name=AdminRoleType.ADMIN, description="General Admin")
            support_role = AdminRole(name=AdminRoleType.SUPPORT_AGENT, description="Support Agent")
            
            db.add_all([super_admin_role, admin_role, support_role])
            await db.commit()
            await db.refresh(super_admin_role)

        admin_email = "rudra@vahan.in"
        admin_password = "Rudra@7877"

        # Create SUPER_ADMIN user
        pwd = get_password_hash(admin_password)
        user = AdminUser(
            full_name="Rudra",
            email=admin_email,
            password_hash=pwd,
            role_id=super_admin_role.id,
            is_active=True
        )
        db.add(user)
        await db.commit()
        
        print(f"Super Admin created: {admin_email}")

if __name__ == "__main__":
    asyncio.run(reset_admin())
