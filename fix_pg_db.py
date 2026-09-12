import asyncio
import asyncpg
import os

async def main():
    db_url = "postgresql://postgres.lckabcseysgzlvkjpgtg:Fleetguard%409411@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres?sslmode=require"
    conn = await asyncpg.connect(db_url)
    
    # Check current version
    version = await conn.fetchval("SELECT version_num FROM alembic_version")
    print(f"Current version in DB: {version}")
    
    # Update to our latest known local version so autogenerate works
    await conn.execute("UPDATE alembic_version SET version_num='8bfb490d091f'")
    print("Updated alembic_version to 8bfb490d091f")
    
    await conn.close()

asyncio.run(main())
