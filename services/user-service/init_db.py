import sqlite3
import hashlib

def init_database():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            balance REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Test users
    test_users = [
        ("alice", "alice@securebank.local", "password123", 0, 1000.0),
        ("bob", "bob@securebank.local", "password456", 0, 500.0),
        ("admin", "admin@securebank.local", "admin123", 1, 10000.0),
    ]
    
    for username, email, password, is_admin, balance in test_users:
        hashed = hashlib.md5(password.encode()).hexdigest()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password, is_admin, balance) VALUES (?, ?, ?, ?, ?)",
                (username, email, hashed, is_admin, balance)
            )
        except sqlite3.IntegrityError:
            print(f"User {username} already exists")
    
    conn.commit()
    conn.close()
    print("✅ Database initialized!")

if __name__ == '__main__':
    init_database()