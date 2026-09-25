import asyncio
from database import engine
from models.driver_domain import Driver
from models.user import User
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession

async def main():
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        for u in users:
            print(f"User {u.id}: {u.full_name} -> company {u.company_id}")
            
        result = await session.execute(select(Driver).where(Driver.last_known_lat.isnot(None)))
        drivers = result.scalars().all()
        for d in drivers:
            print(f"Driver {d.id}: {d.name} -> company {d.company_id} ({d.last_known_lat}, {d.last_known_lng})")

asyncio.run(main())
