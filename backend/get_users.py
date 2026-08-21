import sqlite3
conn = sqlite3.connect('fleetguard.db')
c = conn.cursor()
c.execute("SELECT id, email, mobile_number, is_active FROM users")
for row in c.fetchall():
    print(row)
