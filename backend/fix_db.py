import sqlite3
conn = sqlite3.connect('fleetguard.db')
cursor = conn.cursor()
cursor.execute("UPDATE users SET role='COMPANY_ADMIN' WHERE email='admin@example.com';")
conn.commit()
print("Fixed role")
