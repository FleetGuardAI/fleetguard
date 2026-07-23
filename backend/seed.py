import sqlite3
import bcrypt

def seed():
    # Hash password directly with bcrypt
    password = b"password"
    hashed_pwd = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

    conn = sqlite3.connect('fleetguard.db')
    cursor = conn.cursor()
    
    # Check if admin already exists
    cursor.execute("SELECT id FROM users WHERE email='admin@example.com'")
    if cursor.fetchone():
        print("User already exists.")
        return

    cursor.execute("INSERT INTO companies (company_name, owner_name, mobile_number, email, status) VALUES ('Test Company', 'Admin', '1234567890', 'admin@example.com', 'ACTIVE')")
    company_id = cursor.lastrowid
    
    cursor.execute("INSERT INTO users (company_id, full_name, mobile_number, email, password_hash, role, is_active) VALUES (?, 'Admin User', '1234567890', 'admin@example.com', ?, 'ADMIN', 1)", (company_id, hashed_pwd))
    
    conn.commit()
    print("SEEDED")

if __name__ == '__main__':
    seed()
