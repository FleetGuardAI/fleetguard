"""
Hardware Assets & Universal Telematics Upgrade
Revision ID: a2b3c4d5e6f7
Revises: c91c576a9bba
Create Date: 2026-11-22 19:33:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a2b3c4d5e6f7'
down_revision = 'c91c576a9bba'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())
    existing_cols = {col['name'] for col in inspector.get_columns('assets')} if 'assets' in existing_tables else set()
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('assets')} if 'assets' in existing_tables else set()

    # 1. Add company_id and all hardware & telematics columns to assets table if not present
    if 'company_id' not in existing_cols:
        op.add_column('assets', sa.Column('company_id', sa.Integer(), nullable=True))
    
    col_definitions = [
        ('device_name', sa.Column('device_name', sa.String(length=255), nullable=True)),
        ('imei', sa.Column('imei', sa.String(length=100), nullable=True)),
        ('connection_type', sa.Column('connection_type', sa.String(length=50), server_default='DIRECT_HARDWARE', nullable=False)),
        ('connection_status', sa.Column('connection_status', sa.String(length=50), server_default='PENDING', nullable=False)),
        ('protocol', sa.Column('protocol', sa.String(length=100), nullable=True)),
        ('gps_provider', sa.Column('gps_provider', sa.String(length=100), nullable=True)),
        ('encrypted_credentials', sa.Column('encrypted_credentials', sa.Text(), nullable=True)),
        ('connection_config', sa.Column('connection_config', sa.JSON(), nullable=True)),
        ('last_communication_at', sa.Column('last_communication_at', sa.DateTime(timezone=True), nullable=True)),
        ('last_known_lat', sa.Column('last_known_lat', sa.Float(), nullable=True)),
        ('last_known_lng', sa.Column('last_known_lng', sa.Float(), nullable=True)),
        ('last_known_speed', sa.Column('last_known_speed', sa.Float(), nullable=True)),
        ('last_known_heading', sa.Column('last_known_heading', sa.Float(), nullable=True)),
        ('last_known_ignition', sa.Column('last_known_ignition', sa.Boolean(), nullable=True)),
        ('last_known_battery', sa.Column('last_known_battery', sa.Float(), nullable=True)),
        ('last_known_address', sa.Column('last_known_address', sa.String(length=500), nullable=True)),
        ('installation_date', sa.Column('installation_date', sa.DateTime(timezone=True), nullable=True)),
        ('offline_threshold_minutes', sa.Column('offline_threshold_minutes', sa.Integer(), server_default='15', nullable=False)),
        ('created_at', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)),
        ('updated_at', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)),
    ]

    for col_name, col_obj in col_definitions:
        if col_name not in existing_cols:
            op.add_column('assets', col_obj)

    if 'ix_assets_company_id' not in existing_indexes:
        op.create_index(op.f('ix_assets_company_id'), 'assets', ['company_id'], unique=False)
    if 'ix_assets_imei' not in existing_indexes:
        op.create_index(op.f('ix_assets_imei'), 'assets', ['imei'], unique=False)
    if 'ix_assets_connection_status' not in existing_indexes:
        op.create_index(op.f('ix_assets_connection_status'), 'assets', ['connection_status'], unique=False)
    if 'ix_assets_last_communication_at' not in existing_indexes:
        op.create_index(op.f('ix_assets_last_communication_at'), 'assets', ['last_communication_at'], unique=False)
    
    # 2. Backfill company_id from vehicles if current_vehicle_id is set
    op.execute("""
        UPDATE assets 
        SET company_id = vehicles.company_id 
        FROM vehicles 
        WHERE assets.current_vehicle_id = vehicles.id AND assets.company_id IS NULL
    """)

    # 3. Non-Destructive Reconciliation / Quarantine Strategy:
    # PRESERVE all existing records and historical entries. Never delete orphaned records.
    # If any assets remain unmapped (no vehicle association or invalid company_id),
    # safely reassign them to a dedicated System Quarantine tenant account rather than
    # assigning to arbitrary customer fleets or deleting historical data.
    op.execute("""
        INSERT INTO companies (company_name, owner_name, mobile_number, email, status)
        SELECT 'System Quarantine / Unallocated Fleet', 'System Administrator', '+0000000000', 'quarantine@vahan.system', 'SUSPENDED'
        WHERE NOT EXISTS (
            SELECT 1 FROM companies WHERE email = 'quarantine@vahan.system' OR mobile_number = '+0000000000'
        )
    """)

    op.execute("""
        UPDATE assets 
        SET company_id = (SELECT id FROM companies WHERE email = 'quarantine@vahan.system' LIMIT 1),
            connection_status = 'PENDING',
            operational_status = 'MAINTENANCE'
        WHERE company_id IS NULL OR company_id NOT IN (SELECT id FROM companies)
    """)

    # Record quarantine audit trail in asset_history_records without destroying any existing history
    op.execute("""
        INSERT INTO asset_history_records (asset_id, event_category, performed_at, origin_type, origin_id, details)
        SELECT 
            id, 
            'CALIBRATED', 
            CURRENT_TIMESTAMP, 
            'MIGRATION_QUARANTINE', 
            'SYSTEM', 
            '{"quarantine_reason": "Asset migrated without explicit vehicle or company ownership; safely quarantined under System Administrator for review."}'
        FROM assets 
        WHERE company_id = (SELECT id FROM companies WHERE email = 'quarantine@vahan.system' LIMIT 1)
    """)

    # 4. Add foreign key constraint to companies.id with CASCADE
    existing_fks = {fk['name'] for fk in inspector.get_foreign_keys('assets')} if 'assets' in existing_tables else set()
    if 'fk_assets_company_id_companies' not in existing_fks:
        op.create_foreign_key(
            'fk_assets_company_id_companies',
            'assets',
            'companies',
            ['company_id'],
            ['id'],
            ondelete='CASCADE'
        )

    # 5. Enforce NOT NULL constraint on company_id now that every record is safely reconciled
    op.alter_column('assets', 'company_id', nullable=False)

    # 6. Create gps_provider_accounts table if not present
    if 'gps_provider_accounts' not in existing_tables:
        op.create_table(
            'gps_provider_accounts',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('company_id', sa.Integer(), nullable=False),
            sa.Column('provider_type', sa.String(length=50), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('server_url', sa.String(length=255), nullable=True),
            sa.Column('account_id', sa.String(length=100), nullable=True),
            sa.Column('encrypted_credentials', sa.Text(), nullable=True),
            sa.Column('sync_status', sa.String(length=50), server_default='CONNECTED', nullable=False),
            sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('sync_error', sa.String(length=500), nullable=True),
            sa.Column('device_count', sa.Integer(), server_default='0', nullable=False),
            sa.Column('config', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_gps_provider_accounts_company_id'), 'gps_provider_accounts', ['company_id'], unique=False)


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    if 'gps_provider_accounts' in existing_tables:
        existing_gp_indexes = {idx['name'] for idx in inspector.get_indexes('gps_provider_accounts')}
        if 'ix_gps_provider_accounts_company_id' in existing_gp_indexes:
            op.drop_index(op.f('ix_gps_provider_accounts_company_id'), table_name='gps_provider_accounts')
        op.drop_table('gps_provider_accounts')

    if 'assets' in existing_tables:
        existing_cols = {col['name'] for col in inspector.get_columns('assets')}
        existing_indexes = {idx['name'] for idx in inspector.get_indexes('assets')}
        existing_fks = {fk['name'] for fk in inspector.get_foreign_keys('assets')}

        cols_to_drop = [
            'updated_at', 'created_at', 'offline_threshold_minutes', 'installation_date',
            'last_known_address', 'last_known_battery', 'last_known_ignition',
            'last_known_heading', 'last_known_speed', 'last_known_lng', 'last_known_lat',
            'last_communication_at', 'connection_config', 'encrypted_credentials',
            'gps_provider', 'protocol', 'connection_status', 'connection_type',
            'imei', 'device_name'
        ]

        if 'ix_assets_last_communication_at' in existing_indexes:
            op.drop_index(op.f('ix_assets_last_communication_at'), table_name='assets')
        if 'ix_assets_connection_status' in existing_indexes:
            op.drop_index(op.f('ix_assets_connection_status'), table_name='assets')
        if 'ix_assets_imei' in existing_indexes:
            op.drop_index(op.f('ix_assets_imei'), table_name='assets')

        for col_name in cols_to_drop:
            if col_name in existing_cols:
                op.drop_column('assets', col_name)

        if 'fk_assets_company_id_companies' in existing_fks:
            op.drop_constraint('fk_assets_company_id_companies', 'assets', type_='foreignkey')

        if 'ix_assets_company_id' in existing_indexes:
            op.drop_index(op.f('ix_assets_company_id'), table_name='assets')

        if 'company_id' in existing_cols:
            op.drop_column('assets', 'company_id')
