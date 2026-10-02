import asyncio
import sys
import os
from sqlalchemy import text
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_factory

async def fix_alembic():
    async with async_session_factory() as db:
        await db.execute(text("UPDATE alembic_version SET version_num = 'b35f21696b99' WHERE version_num = '0b92ea0afb29'"))
        await db.commit()
        print("Updated alembic_version table.")

if __name__ == "__main__":
    asyncio.run(fix_alembic())
