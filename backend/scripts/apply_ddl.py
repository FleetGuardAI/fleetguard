import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import engine
from sqlalchemy import text

statements = [
    "ALTER TABLE admin_password_reset_requests ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE SET NULL",
    "ALTER TABLE admin_password_reset_requests ADD COLUMN IF NOT EXISTS token_hash VARCHAR(128)",
    "ALTER TABLE admin_password_reset_requests ADD COLUMN IF NOT EXISTS token_issued_at TIMESTAMPTZ",
    "ALTER TABLE admin_password_reset_requests ADD COLUMN IF NOT EXISTS token_expires_at TIMESTAMPTZ",
    "ALTER TABLE admin_password_reset_requests ADD COLUMN IF NOT EXISTS token_used_at TIMESTAMPTZ",
    "ALTER TABLE admin_password_reset_requests ADD COLUMN IF NOT EXISTS token_revoked_at TIMESTAMPTZ",
    "ALTER TABLE admin_password_reset_requests ADD COLUMN IF NOT EXISTS rejection_reason TEXT",
    "CREATE INDEX IF NOT EXISTS ix_admin_password_reset_requests_token_hash ON admin_password_reset_requests(token_hash)",
    "CREATE INDEX IF NOT EXISTS ix_admin_password_reset_requests_user_id ON admin_password_reset_requests(user_id)",
    "ALTER TABLE password_reset_tokens ADD COLUMN IF NOT EXISTS reset_request_id INTEGER REFERENCES admin_password_reset_requests(id) ON DELETE SET NULL",
    "CREATE INDEX IF NOT EXISTS ix_password_reset_tokens_reset_request_id ON password_reset_tokens(reset_request_id)",
    "UPDATE alembic_version SET version_num = 'b2c3d4e5f6a1'",
]

async def apply_ddl():
    async with engine.begin() as conn:
        for stmt in statements:
            print("Executing:", stmt)
            await conn.execute(text(stmt))
    print("SUCCESS: All DDL statements applied and committed!")

if __name__ == "__main__":
    asyncio.run(apply_ddl())
