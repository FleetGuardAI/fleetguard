import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from database import Base
import models # ensure models are imported

async def test_sqlite():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
            print("SQLite create_all SUCCESS")
        except Exception as e:
            print("SQLite create_all FAILED:", e)

if __name__ == "__main__":
    asyncio.run(test_sqlite())
