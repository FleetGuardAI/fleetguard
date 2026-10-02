import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_factory
from models.admin_domain import AdminUser
from sqlalchemy import select

async def run():
    async with async_session_factory() as db:
        res = await db.execute(select(AdminUser))
        users = res.scalars().all()
        for u in users:
            print(f"User: {u.email} - Active: {u.is_active} - ID: {u.id}")

if __name__ == "__main__":
    asyncio.run(run())
