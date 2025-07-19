import sqlite3
import os

def check_database():
    db_path = 'auth_data.db'
    
    if not os.path.exists(db_path):
        print("Database file does not exist yet.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables in database:")
    for table in tables:
        print(f"- {table[0]}")
    
    # Check data counts
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"Users: {user_count}")
    except:
        print("Users table not found")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM user_data")
        data_count = cursor.fetchone()[0]
        print(f"User Data: {data_count}")
    except:
        print("User Data table not found")
    
    try:
        cursor.execute("SELECT COUNT(*) FROM user_sessions")
        session_count = cursor.fetchone()[0]
        print(f"User Sessions: {session_count}")
    except:
        print("User Sessions table not found")
    
    conn.close()

if __name__ == "__main__":
    check_database() 