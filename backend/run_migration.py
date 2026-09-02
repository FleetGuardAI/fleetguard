import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

async def main():
    engine = create_async_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    async with engine.connect() as base_conn:
        await base_conn.execute(text("SET statement_timeout = 0"))
        
    engine_autocommit = create_async_engine(os.environ["DATABASE_URL"], isolation_level="AUTOCOMMIT")
    async with engine_autocommit.connect() as conn:
        with open('migration_utf8.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
        sql = sql.replace('\ufeff', '')
        
        sql = sql.replace("BEGIN;", "").replace("COMMIT;", "")
        statements = sql.split(";")
        print(f"Executing {len(statements)} SQL statements...", flush=True)
        for i, stmt in enumerate(statements):
            stmt = stmt.strip()
            if not stmt:
                continue
            print(f"Executing {i+1}/{len(statements)}:\n{stmt[:50]}...", flush=True)
            try:
                await conn.execute(text(stmt))
            except Exception as e:
                print(f"Error on {i+1}: {e}", flush=True)
                if 'already exists' in str(e) or 'does not exist' in str(e) or 'already a constraint' in str(e):
                    print("Ignoring error and continuing...")
                    continue
                else:
                    raise
        print("Done!", flush=True)

if __name__ == '__main__':
    asyncio.run(main())
