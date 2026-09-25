import sqlite3
import os

db_path = os.path.join('backend', 'fleetguard.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE alembic_version SET version_num='c121c0718965'")
    conn.commit()
    conn.close()
    print("Fixed alembic version.")
else:
    print("DB not found.")
