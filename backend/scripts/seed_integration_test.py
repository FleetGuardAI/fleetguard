import asyncio
import argparse
from sqlalchemy import text
from database import engine

async def seed_integration_test():
    print("Seeding isolated integration test entities...")
    async with engine.begin() as conn:
        # Create test company
        await conn.execute(text("""
            INSERT INTO companies (id, company_name, owner_name, mobile_number, email, created_at, updated_at) 
            VALUES (9999, 'Integration Test Company', 'Test Owner', '9999999999', 'test9999@fleetguard.com', NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """))
        
        # Create test user/driver
        await conn.execute(text("""
            INSERT INTO users (id, company_id, full_name, email, mobile_number, password_hash, role, is_active, created_at, updated_at)
            VALUES (9999, 9999, 'Integration Test Driver', 'driver9999@test.fleetguard.com', '9999999999', 'mock_hash', 'DRIVER', true, NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET email = 'driver9999@test.fleetguard.com'
        """))
        
        # Create test vehicle
        await conn.execute(text("""
            INSERT INTO vehicles (id, company_id, make, model, year, registration_number, current_status, created_at, updated_at)
            VALUES (9999, 9999, 'Test', 'Mock', 2024, 'TEST-9999', 'AVAILABLE', NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET registration_number = 'TEST-9999'
        """))
        
        # Create active trip to ensure logic fires correctly
        await conn.execute(text("""
            INSERT INTO trips (id, company_id, driver_id, vehicle_id, start_location, end_location, status, actual_start_time, created_at, updated_at)
            VALUES (9999, 9999, 9999, 9999, 'Test Start', 'Test End', 'IN_PROGRESS', NOW() - INTERVAL '1 hour', NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET status = 'IN_PROGRESS'
        """))
        print("Integration test entities seeded successfully (IDs = 9999).")

if __name__ == "__main__":
    asyncio.run(seed_integration_test())
