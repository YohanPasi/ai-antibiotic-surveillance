import os
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Match auth.py config
pwd_context = CryptContext(schemes=["bcrypt", "pbkdf2_sha256"], deprecated="auto")

try:
    with engine.connect() as conn:
        print("Resetting admin password...")
        hashed = pwd_context.hash("Password123")
        conn.execute(text("UPDATE users SET password_hash = :p WHERE username = 'admin'"), 
                     {"p": hashed})
        conn.commit()
        print("✅ Password reset to 'Password123'")

except Exception as e:
    print(f"Error: {e}")
