import asyncio
import asyncpg
import json
import os
from dotenv import load_dotenv

async def inspect():
    load_dotenv()
    db_url = os.environ.get("DATABASE_URL")
    if db_url and db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    
    results = {}
    
    # 1. Check if event_type exists
    results["event_type_exists"] = await conn.fetch('''
        SELECT n.nspname AS schema, t.typname AS type
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE t.typname = 'event_type';
    ''')
    
    # 2. Check event_type values
    results["event_type_values"] = await conn.fetch('''
        SELECT n.nspname AS schema, t.typname AS type, e.enumlabel AS value
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        JOIN pg_enum e ON t.oid = e.enumtypid
        WHERE t.typname = 'event_type'
        ORDER BY e.enumsortorder;
    ''')
    
    # 3. Check alembic_version
    try:
        results["alembic_version"] = await conn.fetch('SELECT * FROM alembic_version;')
    except Exception as e:
        results["alembic_version"] = f"Error: {e}"
        
    # 4. Check all user tables
    results["tables"] = await conn.fetch('''
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schemaname, tablename;
    ''')
    
    # Check all enums
    results["all_enums"] = await conn.fetch('''
        SELECT t.typname AS type
        FROM pg_type t
        JOIN pg_namespace n ON n.oid = t.typnamespace
        WHERE n.nspname = 'public' AND t.typtype = 'e';
    ''')
    
    await conn.close()
    
    def serialize_record(record):
        if hasattr(record, 'items'):
            return dict(record.items())
        return record
        
    for k, v in results.items():
        if isinstance(v, list):
            results[k] = [serialize_record(r) for r in v]
            
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(inspect())
