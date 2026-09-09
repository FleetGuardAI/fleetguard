import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import os
from dotenv import load_dotenv

load_dotenv('.env')

async def repair_metadata():
    url = os.getenv('DATABASE_URL')
    engine = create_async_engine(url)
    
    pre_revision = None
    post_revision = None
    rows_changed = 0
    schema_ok = False
    
    try:
        async with engine.begin() as conn:
            # Step 1: Read-only verification of alembic_version
            result = await conn.execute(text('SELECT version_num FROM alembic_version;'))
            rows = result.fetchall()
            if len(rows) != 1:
                print(f"STOP: alembic_version has {len(rows)} rows, expected 1.")
                raise Exception("Row count mismatch")
                
            pre_revision = rows[0][0]
            if pre_revision != 'b6b360db6af8':
                print(f"STOP: Unexpected version_num {pre_revision}, expected b6b360db6af8.")
                raise Exception("Value mismatch")
                
            # Step 2: Safety Check on schema
            res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'expenses' AND column_name = 'company_id';"))
            if not res.fetchone():
                print("STOP: expenses.company_id not found.")
                raise Exception("Schema mismatch")
                
            res = await conn.execute(text("SELECT is_nullable FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'email';"))
            user_email_row = res.fetchone()
            if not user_email_row or user_email_row[0] != 'YES':
                print("STOP: users.email is not nullable or not found.")
                raise Exception("Schema mismatch")
                
            schema_ok = True
            
            # Step 3: Controlled Metadata Update
            result = await conn.execute(
                text("UPDATE alembic_version SET version_num = 'c121c0718965' WHERE version_num = 'b6b360db6af8';")
            )
            rows_changed = result.rowcount
            if rows_changed != 1:
                print(f"STOP: UPDATE affected {rows_changed} rows, expected 1. Rolling back.")
                raise Exception("Update affected wrong number of rows")
                
        # Connection commits automatically on context manager exit when using engine.begin()
        
        # Step 4: Verify
        async with engine.connect() as conn:
            result = await conn.execute(text('SELECT version_num FROM alembic_version;'))
            rows = result.fetchall()
            post_revision = rows[0][0]
            
        print("SUCCESS")
        print(f"Pre-update: {pre_revision}")
        print(f"Post-update: {post_revision}")
        print(f"Rows changed: {rows_changed}")
        print(f"Schema checked: {schema_ok}")
        
    except Exception as e:
        print(f"FAILED: {e}")
    finally:
        await engine.dispose()

asyncio.run(repair_metadata())
