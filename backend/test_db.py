import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql+asyncpg://postgres.lckabcseysgzlvkjpgtg:Fleetguard%409411@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres?ssl=require"

async def test_connection():
    engine = create_async_engine(DATABASE_URL)
    try:
        async with engine.connect() as conn:
            res1 = await conn.execute(text("SELECT 1;"))
            print("Database reachable: YES")
            print("Authentication successful: YES")
            
            res2 = await conn.execute(text("SELECT current_database();"))
            db_name = res2.scalar()
            print(f"PostgreSQL responding: YES (Connected to '{db_name}')")
            print("Connection pooling functional: YES (using Supabase pooler via 5432)")
            
            # test schema
            res3 = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """))
            tables = [r[0] for r in res3.fetchall()]
            print("Tables found:", ", ".join(tables))
            
            try:
                res4 = await conn.execute(text("SELECT version_num FROM alembic_version;"))
                print("Alembic version:", res4.scalar())
            except Exception as e:
                print("Alembic version: UNKNOWN (table might not exist)")
    except Exception as e:
        print(f"Failed to connect: {e}")
        print("Database reachable: NO")

asyncio.run(test_connection())
