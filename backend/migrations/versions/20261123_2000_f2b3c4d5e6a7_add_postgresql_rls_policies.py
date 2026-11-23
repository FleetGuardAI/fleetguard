"""Add PostgreSQL Row Level Security (RLS) policies for multi-tenant data isolation (FG-SEC-009)

Revision ID: f2b3c4d5e6a7
Revises: e5b6c7d8a9f0
Create Date: 2026-11-23 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f2b3c4d5e6a7'
down_revision: Union[str, None] = 'e5b6c7d8a9f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_TABLES = [
    "vehicles",
    "trips",
    "fuel_transactions",
    "expenses",
    "maintenance_records",
    "tyres",
    "driver_locations",
    "operational_events",
    "copilot_conversations",
    "documents",
    "tickets",
    "fleet_invites",
    "vehicle_inspections",
    "owner_pairing_tokens",
    "driver_qualifications",
    "notifications",
]


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        # RLS is PostgreSQL-specific; SQLite and test in-memory dialects skip gracefully
        return

    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    for table in TENANT_TABLES:
        if table in existing_tables:
            # Enable RLS and force it even for table owners/superusers
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
            op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

            # Drop existing policy if already present to guarantee idempotency
            op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};")

            # Create policy checking current_setting('app.current_company_id')
            op.execute(f"""
                CREATE POLICY {table}_tenant_isolation_policy ON {table}
                FOR ALL
                USING (
                    current_setting('app.is_super_admin', true) = 'true'
                    OR company_id = NULLIF(current_setting('app.current_company_id', true), '')::integer
                )
                WITH CHECK (
                    current_setting('app.is_super_admin', true) = 'true'
                    OR company_id = NULLIF(current_setting('app.current_company_id', true), '')::integer
                );
            """)

    # Special policy for copilot_messages (joins copilot_conversations on conversation_id)
    if "copilot_messages" in existing_tables and "copilot_conversations" in existing_tables:
        op.execute("ALTER TABLE copilot_messages ENABLE ROW LEVEL SECURITY;")
        op.execute("ALTER TABLE copilot_messages FORCE ROW LEVEL SECURITY;")
        op.execute("DROP POLICY IF EXISTS copilot_messages_tenant_isolation_policy ON copilot_messages;")
        op.execute("""
            CREATE POLICY copilot_messages_tenant_isolation_policy ON copilot_messages
            FOR ALL
            USING (
                current_setting('app.is_super_admin', true) = 'true'
                OR conversation_id IN (
                    SELECT id FROM copilot_conversations
                    WHERE company_id = NULLIF(current_setting('app.current_company_id', true), '')::integer
                )
            )
            WITH CHECK (
                current_setting('app.is_super_admin', true) = 'true'
                OR conversation_id IN (
                    SELECT id FROM copilot_conversations
                    WHERE company_id = NULLIF(current_setting('app.current_company_id', true), '')::integer
                )
            );
        """)


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    if "copilot_messages" in existing_tables:
        op.execute("DROP POLICY IF EXISTS copilot_messages_tenant_isolation_policy ON copilot_messages;")
        op.execute("ALTER TABLE copilot_messages NO FORCE ROW LEVEL SECURITY;")
        op.execute("ALTER TABLE copilot_messages DISABLE ROW LEVEL SECURITY;")

    for table in TENANT_TABLES:
        if table in existing_tables:
            op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};")
            op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

