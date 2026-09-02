"""Add company_id to operational_events with backfill

Revision ID: f320ff2e7118
Revises: 4ea8680531d5
Create Date: 2026-08-30 15:08:26.723060

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f320ff2e7118'
down_revision: Union[str, None] = '4ea8680531d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add column as nullable
    op.add_column('operational_events', sa.Column('company_id', sa.Integer(), nullable=True))
    
    conn = op.get_bind()
    
    # 2. Fetch all events
    res = conn.execute(sa.text("SELECT id, entity_type, entity_id FROM operational_events"))
    events = res.fetchall()
    
    # 3. Backfill company_id
    for e_id, e_type, entity_id in events:
        company_id = None
        if e_type == 'VEHICLE':
            if str(entity_id).isdigit():
                r = conn.execute(sa.text(f"SELECT company_id FROM vehicles WHERE id = {int(entity_id)}"))
            else:
                r = conn.execute(sa.text(f"SELECT company_id FROM vehicles WHERE registration_number = '{entity_id}'"))
            row = r.fetchone()
            if row: company_id = row[0]
        elif e_type == 'DRIVER':
            if str(entity_id).isdigit() and len(str(entity_id)) < 10:
                r = conn.execute(sa.text(f"SELECT company_id FROM drivers WHERE id = {int(entity_id)}"))
                row = r.fetchone()
                if row: company_id = row[0]
            elif str(entity_id).isdigit() and len(str(entity_id)) == 10:
                # Match phone number
                r = conn.execute(sa.text(f"SELECT company_id FROM drivers WHERE phone_number = '{entity_id}' OR phone_number LIKE '%{entity_id}'"))
                row = r.fetchone()
                if row: company_id = row[0]
            else:
                r = conn.execute(sa.text(f"SELECT company_id FROM drivers WHERE employee_id = '{entity_id}'"))
                row = r.fetchone()
                if row: company_id = row[0]
        elif e_type == 'TRIP':
            r = conn.execute(sa.text(f"SELECT company_id FROM trips WHERE id = {int(entity_id)}"))
            row = r.fetchone()
            if row: company_id = row[0]
        elif e_type == 'EXPENSE':
            r = conn.execute(sa.text(f"SELECT company_id FROM expenses WHERE id = {int(entity_id)}"))
            row = r.fetchone()
            if row: company_id = row[0]
        elif e_type == 'DOCUMENT':
            r = conn.execute(sa.text(f"SELECT company_id FROM documents WHERE id = '{entity_id}'"))
            row = r.fetchone()
            if row: company_id = row[0]

        if company_id is None:
            raise Exception(f"Failed to map OperationalEvent {e_id} (Type: {e_type}, ID: {entity_id}) to a company_id. Aborting migration.")
        
        # Update record
        conn.execute(sa.text(f"UPDATE operational_events SET company_id = {company_id} WHERE id = '{e_id}'"))
        
    # 4. Make column NOT NULL
    op.alter_column('operational_events', 'company_id', existing_type=sa.Integer(), nullable=False)
    
    # 5. Add foreign key and index
    op.create_index(op.f('ix_operational_events_company_id'), 'operational_events', ['company_id'], unique=False)
    op.create_foreign_key('fk_operational_events_company_id_companies', 'operational_events', 'companies', ['company_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    op.drop_constraint('fk_operational_events_company_id_companies', 'operational_events', type_='foreignkey')
    op.drop_index(op.f('ix_operational_events_company_id'), table_name='operational_events')
    op.drop_column('operational_events', 'company_id')
