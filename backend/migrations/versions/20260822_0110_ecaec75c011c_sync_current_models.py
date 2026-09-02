"""sync_current_models

Revision ID: ecaec75c011c
Revises: c2557519ddca
Create Date: 2026-08-22 01:10:55.690868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ecaec75c011c'
down_revision: Union[str, None] = 'c2557519ddca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. evidence
    op.create_table(
        'evidence',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('evidence_type', sa.Enum('RECEIPT_DOCUMENT', 'OCR_EXTRACTION', 'GPS_LOCATION', 'FUEL_SENSOR', 'DRIVER_HISTORY', 'VEHICLE_HISTORY', 'MANUAL_VERIFICATION', name='evidencetype', native_enum=False, length=50), nullable=False),
        sa.Column('source', sa.String(length=255), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'COMPLETED', 'FAILED', name='evidencestatus', native_enum=False, length=50), server_default='PENDING', nullable=False),
        sa.Column('summary', sa.String(length=500), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('raw_data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['operational_events.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_evidence_id'), 'evidence', ['id'], unique=False)
    op.create_index(op.f('ix_evidence_event_id'), 'evidence', ['event_id'], unique=False)
    op.create_index(op.f('ix_evidence_evidence_type'), 'evidence', ['evidence_type'], unique=False)
    op.create_index(op.f('ix_evidence_status'), 'evidence', ['status'], unique=False)

    # 2. processed_events
    op.create_table(
        'processed_events',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('operational_event_id', sa.String(length=36), nullable=False),
        sa.Column('domain_name', sa.String(length=255), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processing_result', sa.String(length=50), nullable=False),
        sa.Column('metadata_payload', sa.JSON(), nullable=True),
        sa.UniqueConstraint('operational_event_id', 'domain_name', name='uq_processed_events_event_id_domain')
    )
    op.create_index(op.f('ix_processed_events_domain_name'), 'processed_events', ['domain_name'], unique=False)
    op.create_index(op.f('ix_processed_events_operational_event_id'), 'processed_events', ['operational_event_id'], unique=False)

    # 3. outbox_events
    op.create_table(
        'outbox_events',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('event_id', sa.String(length=36), nullable=True),
        sa.Column('topic', sa.String(length=255), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('headers', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PUBLISHING', 'PUBLISHED', name='outboxstatus', native_enum=False, length=50), server_default='PENDING', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_error', sa.String(), nullable=True)
    )
    op.create_index(op.f('ix_outbox_events_event_id'), 'outbox_events', ['event_id'], unique=False)
    op.create_index(op.f('ix_outbox_events_status'), 'outbox_events', ['status'], unique=False)

    # 4. documents
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('storage_path', sa.String(length=1024), nullable=False),
        sa.Column('status', sa.Enum('UPLOADED', 'STORED', 'AVAILABLE', 'FAILED', name='documentstoragestatus', native_enum=False, length=50), server_default='UPLOADED', nullable=False),
        sa.Column('uploaded_by', sa.String(length=255), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False)
    )
    op.create_index(op.f('ix_documents_id'), 'documents', ['id'], unique=False)
    op.create_index(op.f('ix_documents_company_id'), 'documents', ['company_id'], unique=False)
    op.create_index(op.f('ix_documents_status'), 'documents', ['status'], unique=False)

    # 5. fleet_invites
    op.create_table(
        'fleet_invites',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('invite_token', sa.String(length=255), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('use_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('invite_token')
    )
    op.create_index(op.f('ix_fleet_invites_company_id'), 'fleet_invites', ['company_id'], unique=False)
    op.create_index(op.f('ix_fleet_invites_invite_token'), 'fleet_invites', ['invite_token'], unique=True)

    # 6. driver_locations
    op.create_table(
        'driver_locations',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('heading', sa.Float(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('battery_percent', sa.Integer(), nullable=True),
        sa.Column('activity_state', sa.String(length=50), nullable=True),
        sa.Column('source', sa.Enum('PHONE_GPS', 'HARDWARE_GPS', name='locationsource', native_enum=False, length=50), server_default='PHONE_GPS', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_driver_locations_company_id'), 'driver_locations', ['company_id'], unique=False)
    op.create_index(op.f('ix_driver_locations_driver_id'), 'driver_locations', ['driver_id'], unique=False)
    op.create_index(op.f('ix_driver_locations_timestamp'), 'driver_locations', ['timestamp'], unique=False)

    # 7. location_alerts
    op.create_table(
        'location_alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.Enum('GPS_DRIFT', 'SPEED_VIOLATION', 'GEOFENCE_ENTRY', 'GEOFENCE_EXIT', 'SIGNAL_LOST', name='alerttype', native_enum=False, length=50), nullable=False),
        sa.Column('details', sa.String(length=500), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_location_alerts_alert_type'), 'location_alerts', ['alert_type'], unique=False)
    op.create_index(op.f('ix_location_alerts_company_id'), 'location_alerts', ['company_id'], unique=False)
    op.create_index(op.f('ix_location_alerts_driver_id'), 'location_alerts', ['driver_id'], unique=False)

    # 8. vehicle_inspections
    op.create_table(
        'vehicle_inspections',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('inspection_type', sa.Enum('PRE_TRIP', 'POST_TRIP', name='inspectiontype', native_enum=False, length=50), nullable=False),
        sa.Column('overall_status', sa.Enum('PASS', 'FAIL', 'PARTIAL', name='inspectionstatus', native_enum=False, length=50), server_default='PASS', nullable=False),
        sa.Column('items', sa.JSON(), nullable=False),
        sa.Column('notes', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_vehicle_inspections_company_id'), 'vehicle_inspections', ['company_id'], unique=False)
    op.create_index(op.f('ix_vehicle_inspections_driver_id'), 'vehicle_inspections', ['driver_id'], unique=False)
    op.create_index(op.f('ix_vehicle_inspections_inspection_type'), 'vehicle_inspections', ['inspection_type'], unique=False)
    op.create_index(op.f('ix_vehicle_inspections_vehicle_id'), 'vehicle_inspections', ['vehicle_id'], unique=False)

    # 9. proof_of_delivery
    op.create_table(
        'proof_of_delivery',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('trip_id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('signature_url', sa.String(length=500), nullable=True),
        sa.Column('photos', sa.JSON(), nullable=True),
        sa.Column('invoice_url', sa.String(length=500), nullable=True),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('receiver_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_proof_of_delivery_company_id'), 'proof_of_delivery', ['company_id'], unique=False)
    op.create_index(op.f('ix_proof_of_delivery_driver_id'), 'proof_of_delivery', ['driver_id'], unique=False)
    op.create_index(op.f('ix_proof_of_delivery_trip_id'), 'proof_of_delivery', ['trip_id'], unique=False)

    # 10. emergency_alerts
    op.create_table(
        'emergency_alerts',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=True),
        sa.Column('trip_id', sa.Integer(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'ACKNOWLEDGED', 'RESOLVED', name='emergencystatus', native_enum=False, length=50), server_default='ACTIVE', nullable=False),
        sa.Column('message', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], )
    )
    op.create_index(op.f('ix_emergency_alerts_company_id'), 'emergency_alerts', ['company_id'], unique=False)
    op.create_index(op.f('ix_emergency_alerts_driver_id'), 'emergency_alerts', ['driver_id'], unique=False)
    op.create_index(op.f('ix_emergency_alerts_status'), 'emergency_alerts', ['status'], unique=False)

    # 11. wallet_transactions
    op.create_table(
        'wallet_transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.Enum('SALARY', 'ADVANCE', 'INCENTIVE', 'DEDUCTION', 'REPAYMENT', name='transactiontype', native_enum=False, length=50), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'APPROVED', 'REJECTED', 'COMPLETED', name='transactionstatus', native_enum=False, length=50), server_default='PENDING', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('reference_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='CASCADE')
    )
    op.create_index(op.f('ix_wallet_transactions_company_id'), 'wallet_transactions', ['company_id'], unique=False)
    op.create_index(op.f('ix_wallet_transactions_driver_id'), 'wallet_transactions', ['driver_id'], unique=False)
    op.create_index(op.f('ix_wallet_transactions_transaction_type'), 'wallet_transactions', ['transaction_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_wallet_transactions_transaction_type'), table_name='wallet_transactions')
    op.drop_index(op.f('ix_wallet_transactions_driver_id'), table_name='wallet_transactions')
    op.drop_index(op.f('ix_wallet_transactions_company_id'), table_name='wallet_transactions')
    op.drop_table('wallet_transactions')
    op.execute("DROP TYPE transactiontype;")
    op.execute("DROP TYPE transactionstatus;")

    op.drop_index(op.f('ix_emergency_alerts_status'), table_name='emergency_alerts')
    op.drop_index(op.f('ix_emergency_alerts_driver_id'), table_name='emergency_alerts')
    op.drop_index(op.f('ix_emergency_alerts_company_id'), table_name='emergency_alerts')
    op.drop_table('emergency_alerts')
    op.execute("DROP TYPE emergencystatus;")

    op.drop_index(op.f('ix_proof_of_delivery_trip_id'), table_name='proof_of_delivery')
    op.drop_index(op.f('ix_proof_of_delivery_driver_id'), table_name='proof_of_delivery')
    op.drop_index(op.f('ix_proof_of_delivery_company_id'), table_name='proof_of_delivery')
    op.drop_table('proof_of_delivery')

    op.drop_index(op.f('ix_vehicle_inspections_vehicle_id'), table_name='vehicle_inspections')
    op.drop_index(op.f('ix_vehicle_inspections_inspection_type'), table_name='vehicle_inspections')
    op.drop_index(op.f('ix_vehicle_inspections_driver_id'), table_name='vehicle_inspections')
    op.drop_index(op.f('ix_vehicle_inspections_company_id'), table_name='vehicle_inspections')
    op.drop_table('vehicle_inspections')
    op.execute("DROP TYPE inspectiontype;")
    op.execute("DROP TYPE inspectionstatus;")

    op.drop_index(op.f('ix_location_alerts_driver_id'), table_name='location_alerts')
    op.drop_index(op.f('ix_location_alerts_company_id'), table_name='location_alerts')
    op.drop_index(op.f('ix_location_alerts_alert_type'), table_name='location_alerts')
    op.drop_table('location_alerts')
    op.execute("DROP TYPE alerttype;")

    op.drop_index(op.f('ix_driver_locations_timestamp'), table_name='driver_locations')
    op.drop_index(op.f('ix_driver_locations_driver_id'), table_name='driver_locations')
    op.drop_index(op.f('ix_driver_locations_company_id'), table_name='driver_locations')
    op.drop_table('driver_locations')
    op.execute("DROP TYPE locationsource;")

    op.drop_index(op.f('ix_fleet_invites_invite_token'), table_name='fleet_invites')
    op.drop_index(op.f('ix_fleet_invites_company_id'), table_name='fleet_invites')
    op.drop_table('fleet_invites')

    op.drop_index(op.f('ix_documents_status'), table_name='documents')
    op.drop_index(op.f('ix_documents_company_id'), table_name='documents')
    op.drop_index(op.f('ix_documents_id'), table_name='documents')
    op.drop_table('documents')
    op.execute("DROP TYPE documentstoragestatus;")

    op.drop_index(op.f('ix_outbox_events_status'), table_name='outbox_events')
    op.drop_index(op.f('ix_outbox_events_event_id'), table_name='outbox_events')
    op.drop_table('outbox_events')
    op.execute("DROP TYPE outboxstatus;")

    op.drop_index(op.f('ix_processed_events_operational_event_id'), table_name='processed_events')
    op.drop_index(op.f('ix_processed_events_domain_name'), table_name='processed_events')
    op.drop_table('processed_events')

    op.drop_index(op.f('ix_evidence_status'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_evidence_type'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_event_id'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_id'), table_name='evidence')
    op.drop_table('evidence')
    op.execute("DROP TYPE evidencetype;")
    op.execute("DROP TYPE evidencestatus;")
