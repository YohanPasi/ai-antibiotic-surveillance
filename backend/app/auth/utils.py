from datetime import datetime, timedelta
from jose import jwt
import bcrypt
from ..config import settings

def hash_password(password: str) -> str:
    # Ensure password is a string
    if isinstance(password, bytes):
        password = password.decode('utf-8')
    # Encode to bytes for bcrypt (bcrypt limit is 72 bytes)
    password_bytes = password.encode('utf-8')[:72]
    # Generate salt and hash
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    # Ensure password is a string
    if isinstance(password, bytes):
        password = password.decode('utf-8')
    # Encode to bytes
    password_bytes = password.encode('utf-8')[:72]
    hashed_bytes = hashed.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def create_access_token(data: dict, expires_minutes=60):
    expire = datetime.utcnow() + timedelta(minutes=expires_minutes)
    data.update({"exp": expire})
    
    token = jwt.encode(
        data,
        settings.secret_key,
        algorithm=settings.jwt_algorithm
    )
    return token
