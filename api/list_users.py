import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id, username, role, is_active FROM users"))
        users = result.fetchall()
        print("\n--- USERS ---")
        for u in users:
            print(f"User: {u[1]} | Role: {u[2]} | Active: {u[3]}")
            
        if not users:
            print("No users found! Creating admin.")
            # Create admin manually if missing
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed = pwd_context.hash("Password123")
            conn.execute(text("INSERT INTO users (username, password_hash, role, is_active) VALUES (:u, :p, :r, :a)"), 
                         {"u": "admin", "p": hashed, "r": "admin", "a": True})
            conn.commit()
            print("Created admin/Password123")

except Exception as e:
    print(f"Error: {e}")
