"""fix_ticket_enums

Revision ID: c2557519ddca
Revises: d4e5f6g7h8i9
Create Date: 2026-08-20 18:06:59.264981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2557519ddca'
down_revision: Union[str, None] = 'd4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Rename old types
    op.execute("ALTER TYPE ticketstatus RENAME TO old_ticketstatus")
    op.execute("ALTER TYPE risklevel RENAME TO old_risklevel")
    
    # 2. Create new types matching Python enum values exactly
    op.execute("CREATE TYPE ticketstatus AS ENUM('pending', 'approved', 'rejected')")
    op.execute("CREATE TYPE risklevel AS ENUM('Low', 'Medium', 'High', 'Critical')")
    
    # 3. Alter columns to use new types with safe mapping
    op.execute("""
        ALTER TABLE tickets 
        ALTER COLUMN status TYPE ticketstatus 
        USING CASE status::text 
            WHEN 'OPEN' THEN 'pending'::ticketstatus 
            WHEN 'IN_PROGRESS' THEN 'pending'::ticketstatus
            WHEN 'RESOLVED' THEN 'approved'::ticketstatus
            WHEN 'CLOSED' THEN 'approved'::ticketstatus
            WHEN 'REJECTED' THEN 'rejected'::ticketstatus
            ELSE 'pending'::ticketstatus 
        END
    """)
    op.execute("""
        ALTER TABLE tickets 
        ALTER COLUMN risk_level TYPE risklevel 
        USING CASE risk_level::text 
            WHEN 'LOW' THEN 'Low'::risklevel 
            WHEN 'MEDIUM' THEN 'Medium'::risklevel
            WHEN 'HIGH' THEN 'High'::risklevel
            WHEN 'CRITICAL' THEN 'Critical'::risklevel
            ELSE 'Low'::risklevel 
        END
    """)
    
    # 4. Drop the old types safely
    op.execute("DROP TYPE old_ticketstatus")
    op.execute("DROP TYPE old_risklevel")


def downgrade() -> None:
    # 1. Rename new types
    op.execute("ALTER TYPE ticketstatus RENAME TO new_ticketstatus")
    op.execute("ALTER TYPE risklevel RENAME TO new_risklevel")
    
    # 2. Create old types
    op.execute("CREATE TYPE ticketstatus AS ENUM('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'REJECTED')")
    op.execute("CREATE TYPE risklevel AS ENUM('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')")
    
    # 3. Alter columns back
    op.execute("""
        ALTER TABLE tickets 
        ALTER COLUMN status TYPE ticketstatus 
        USING CASE status::text 
            WHEN 'pending' THEN 'OPEN'::ticketstatus 
            WHEN 'approved' THEN 'CLOSED'::ticketstatus
            WHEN 'rejected' THEN 'REJECTED'::ticketstatus
            ELSE 'OPEN'::ticketstatus 
        END
    """)
    op.execute("""
        ALTER TABLE tickets 
        ALTER COLUMN risk_level TYPE risklevel 
        USING CASE risk_level::text 
            WHEN 'Low' THEN 'LOW'::risklevel 
            WHEN 'Medium' THEN 'MEDIUM'::risklevel
            WHEN 'High' THEN 'HIGH'::risklevel
            WHEN 'Critical' THEN 'CRITICAL'::risklevel
            ELSE 'LOW'::risklevel 
        END
    """)
    
    # 4. Drop the new types
    op.execute("DROP TYPE new_ticketstatus")
    op.execute("DROP TYPE new_risklevel")
