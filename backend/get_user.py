import asyncio
from sqlalchemy import select
from database import async_session
from models.user import User

async def run():
    async with async_session() as s:
        res = await s.execute(select(User.email).limit(1))
        print(res.scalar())

if __name__ == '__main__':
    asyncio.run(run())
