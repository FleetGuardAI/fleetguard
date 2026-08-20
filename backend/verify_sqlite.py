import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./e2e_test.db"

import asyncio
import logging
from config import settings
from database import Base, engine
import models # ensure all models are imported

async def create_db():
    print(f"DATABASE_URL is {settings.DATABASE_URL}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("All tables created successfully.")

if __name__ == "__main__":
    asyncio.run(create_db())
