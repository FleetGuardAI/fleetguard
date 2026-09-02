import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

async def main():
    engine = create_async_engine(os.environ["DATABASE_URL"])
    async with engine.connect() as conn:
        await conn.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid <> pg_backend_pid() AND datname = current_database() AND usename = current_user"))
        await conn.commit()
    print('Connections killed')

if __name__ == '__main__':
    asyncio.run(main())
