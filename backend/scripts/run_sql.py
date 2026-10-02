import asyncio
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_factory

async def run_sql():
    with open("migrations.sql", "r", encoding="utf-16") as f:
        sql = f.read()
    
    statements = [s.strip() for s in sql.split(";") if s.strip()]
    
    async with async_session_factory() as db:
        for stmt in statements:
            if stmt.upper().startswith("BEGIN") or stmt.upper().startswith("COMMIT"):
                continue
            try:
                await db.execute(text(stmt))
            except Exception as e:
                print(f"Skipping failed statement:\n{stmt}\nError: {e}\n")
                # rollback the aborted transaction state for this session so we can continue
                await db.rollback()
        
        # force commit at the end
        await db.commit()
        print("Successfully finished executing migrations.sql")

if __name__ == "__main__":
    asyncio.run(run_sql())
