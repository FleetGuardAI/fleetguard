import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

metadata = sa.MetaData()

# Test with postgresql.ENUM
t1 = sa.Table(
    't1', metadata,
    sa.Column('e1', postgresql.ENUM('a', 'b', name='my_enum', create_type=False))
)

# Test with sa.Enum
t2 = sa.Table(
    't2', metadata,
    sa.Column('e2', sa.Enum('a', 'b', name='my_enum2', create_type=False))
)

from sqlalchemy.ext.asyncio import create_async_engine
import asyncio

async def test():
    engine = create_async_engine("postgresql+asyncpg://postgres.ovxsxpjkezsfsfhfhcno:Fleetguardai%409411@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres")
    async with engine.begin() as conn:
        print("SQL for t1:")
        await conn.run_sync(lambda sync_conn: metadata.create_all(sync_conn, tables=[t1]))
        print("SQL for t2:")
        await conn.run_sync(lambda sync_conn: metadata.create_all(sync_conn, tables=[t2]))

if __name__ == "__main__":
    pass # we don't need to run it against db, just compile it
    from sqlalchemy.dialects import postgresql as pg_dialect
    print(CreateTable(t1).compile(dialect=pg_dialect.dialect()))
    print(CreateTable(t2).compile(dialect=pg_dialect.dialect()))

