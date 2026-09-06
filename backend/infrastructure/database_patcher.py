import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("fleetguard.database_patcher")

async def apply_schema_patches(session: AsyncSession):
    """
    Safely applies schema patches (adding missing columns) 
    for databases where Alembic isn't fully managing incremental changes.
    """
    logger.info("🔧 Running database schema patcher...")
    
    # Define the patches we want to apply:
    # Format: "table_name": [("column_name", "sql_type")]
    patches = {
        "vehicles": [
            ("rc_url", "VARCHAR(500)"),
            ("insurance_url", "VARCHAR(500)"),
            ("insurance_expiry", "DATE"),
            ("puc_url", "VARCHAR(500)"),
            ("puc_expiry", "DATE"),
            ("fitness_url", "VARCHAR(500)"),
            ("fitness_expiry", "DATE"),
            ("permit_url", "VARCHAR(500)"),
            ("permit_expiry", "DATE"),
        ],
        "trips": [
            ("start_selfie_url", "VARCHAR(500)"),
            ("revenue", "FLOAT"),
            ("planned_cost", "FLOAT"),
            ("planned_fuel_liters", "FLOAT"),
            ("cargo_weight", "FLOAT"),
        ],
        "drivers": [
            ("company_id", "INTEGER"),
            ("user_id", "INTEGER"),
            ("license_front_url", "VARCHAR(500)"),
            ("license_back_url", "VARCHAR(500)"),
            ("aadhaar_front_url", "VARCHAR(500)"),
            ("aadhaar_back_url", "VARCHAR(500)"),
            ("selfie_url", "VARCHAR(500)"),
            ("aadhaar_number", "VARCHAR(20)"),
            ("verification_status", "VARCHAR(50)"),
            ("face_verified", "BOOLEAN"),
            ("duty_status", "VARCHAR(50)"),
            ("last_known_lat", "FLOAT"),
            ("last_known_lng", "FLOAT"),
            ("last_location_at", "TIMESTAMP WITH TIME ZONE"),
            ("fcm_token", "VARCHAR(500)"),
        ]
    }
    
    from sqlalchemy.exc import ProgrammingError
    
    try:
        for table, columns in patches.items():
            for col_name, col_type in columns:
                query = text(f"ALTER TABLE IF EXISTS {table} ADD COLUMN IF NOT EXISTS {col_name} {col_type}")
                try:
                    await session.execute(query)
                except ProgrammingError as pe:
                    # Log table not found or other specific SQL errors
                    logger.warning(f"⚠️ Could not patch column {col_name} on {table}. It may not exist yet. Error: {pe}")
                except Exception as e:
                    logger.error(f"❌ Unexpected error patching {table}.{col_name}: {e}")
                
        await session.commit()
        logger.info("✅ Database schema patcher completed successfully.")
    except Exception as e:
        await session.rollback()
        logger.error(f"❌ Database schema patcher failed during execution: {e}")
        # We do not raise the exception so we don't crash application startup, 
        # but we have logged the full error safely.
