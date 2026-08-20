import sqlite3

conn = sqlite3.connect('fleetguard.db')
c = conn.cursor()

c.execute("SELECT * FROM trips LIMIT 5;")
print("TRIPS:")
for row in c.fetchall():
    print(row)

c.execute("SELECT * FROM fuel_transactions LIMIT 5;")
print("FUEL TRANSACTIONS:")
for row in c.fetchall():
    print(row)
