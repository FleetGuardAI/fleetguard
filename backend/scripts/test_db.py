import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_factory
from sqlalchemy import text

async def main():
    async with async_session_factory() as s:
        try:
            result = await s.execute(text('SELECT * FROM admin_roles'))
            print("Table exists! Rows:", result.fetchall())
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
