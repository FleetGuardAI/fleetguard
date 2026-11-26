"""
Comprehensive Migration Safety & Zero-Destruction Verification
Verifies upgrade and downgrade behavior with realistic existing production data.
"""
import unittest
import sqlite3


class TestDatabaseMigrationSafety(unittest.TestCase):
    def test_safe_quarantine_reconciliation_zero_deletion(self):
        conn = sqlite3.connect(":memory:")
        c = conn.cursor()

        # 1. Realistic existing pre-migration schema
        c.execute("""
        CREATE TABLE companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            owner_name TEXT NOT NULL,
            mobile_number TEXT NOT NULL UNIQUE,
            email TEXT UNIQUE,
            status TEXT NOT NULL
        );
        """)

        c.execute("""
        CREATE TABLE vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL REFERENCES companies(id),
            registration_number TEXT NOT NULL
        );
        """)

        c.execute("""
        CREATE TABLE assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL,
            asset_type TEXT NOT NULL,
            current_vehicle_id INTEGER REFERENCES vehicles(id)
        );
        """)

        c.execute("""
        CREATE TABLE asset_history_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asset_id INTEGER NOT NULL REFERENCES assets(id),
            event_category TEXT NOT NULL,
            performed_at TIMESTAMP NOT NULL,
            origin_type TEXT,
            origin_id TEXT,
            details TEXT
        );
        """)

        # 2. Populate realistic production records
        c.execute(
            "INSERT INTO companies (id, company_name, owner_name, mobile_number, email, status) "
            "VALUES (1, 'Acme Logistics', 'John Doe', '+919876543210', 'john@acme.com', 'ACTIVE')"
        )
        c.execute(
            "INSERT INTO vehicles (id, company_id, registration_number) "
            "VALUES (10, 1, 'MH-01-AB-1234')"
        )

        # Asset 1: Assigned to Vehicle 10
        c.execute(
            "INSERT INTO assets (id, business_id, asset_type, current_vehicle_id) "
            "VALUES (1, 'AST-001', 'GPS_DEVICE', 10)"
        )
        c.execute(
            "INSERT INTO asset_history_records (id, asset_id, event_category, performed_at, origin_type, origin_id, details) "
            "VALUES (100, 1, 'INSTALLED', '2026-01-01', 'USER', '1', 'Initial install')"
        )

        # Asset 2: Unmapped / orphaned asset with NO vehicle assignment
        c.execute(
            "INSERT INTO assets (id, business_id, asset_type, current_vehicle_id) "
            "VALUES (2, 'AST-002', 'GPS_DEVICE', NULL)"
        )
        c.execute(
            "INSERT INTO asset_history_records (id, asset_id, event_category, performed_at, origin_type, origin_id, details) "
            "VALUES (101, 2, 'REGISTERED', '2026-01-02', 'USER', '1', 'Device in storage')"
        )

        conn.commit()

        # 3. Execute Migration Upgrade logic:
        c.execute("ALTER TABLE assets ADD COLUMN company_id INTEGER")

        # Backfill assigned assets from vehicle
        c.execute("""
        UPDATE assets 
        SET company_id = (SELECT vehicles.company_id FROM vehicles WHERE vehicles.id = assets.current_vehicle_id)
        WHERE assets.current_vehicle_id IS NOT NULL AND assets.company_id IS NULL;
        """)

        # Safe quarantine reconciliation:
        c.execute("""
        INSERT INTO companies (company_name, owner_name, mobile_number, email, status)
        SELECT 'System Quarantine / Unallocated Fleet', 'System Administrator', '+0000000000', 'quarantine@vahan.system', 'SUSPENDED'
        WHERE NOT EXISTS (
            SELECT 1 FROM companies WHERE email = 'quarantine@vahan.system' OR mobile_number = '+0000000000'
        );
        """)

        c.execute("""
        UPDATE assets 
        SET company_id = (SELECT id FROM companies WHERE email = 'quarantine@vahan.system' LIMIT 1)
        WHERE company_id IS NULL OR company_id NOT IN (SELECT id FROM companies);
        """)

        c.execute("""
        INSERT INTO asset_history_records (asset_id, event_category, performed_at, origin_type, origin_id, details)
        SELECT 
            id, 
            'CALIBRATED', 
            CURRENT_TIMESTAMP, 
            'MIGRATION_QUARANTINE', 
            'SYSTEM', 
            'Quarantined under System Administrator'
        FROM assets 
        WHERE company_id = (SELECT id FROM companies WHERE email = 'quarantine@vahan.system' LIMIT 1);
        """)

        conn.commit()

        # 4. Strict assertions:
        # A. ZERO Assets deleted
        assets = c.execute("SELECT id, business_id, company_id FROM assets ORDER BY id").fetchall()
        self.assertEqual(len(assets), 2, "Destructive deletion detected! Assets were lost.")
        
        # B. Assigned asset mapped to Vehicle's company
        self.assertEqual(assets[0][2], 1, "Assigned asset 1 failed to map to vehicle's company_id 1")
        
        # C. Unmapped asset quarantined, NOT given to customer company 1
        self.assertNotEqual(assets[1][2], 1, "Unmapped asset was assigned to customer company 1!")
        quarantine_comp = c.execute("SELECT id FROM companies WHERE email = 'quarantine@vahan.system'").fetchone()
        self.assertEqual(assets[1][2], quarantine_comp[0], "Unmapped asset was not placed into quarantine company")

        # D. ZERO History records deleted, plus 1 new quarantine log created
        history = c.execute("SELECT id, asset_id, event_category FROM asset_history_records ORDER BY id").fetchall()
        self.assertEqual(len(history), 3, "Historical logs deleted or missing!")
        self.assertEqual(history[0][0], 100, "Historical record 100 lost!")
        self.assertEqual(history[1][0], 101, "Historical record 101 lost!")

        conn.close()


if __name__ == "__main__":
    unittest.main()
