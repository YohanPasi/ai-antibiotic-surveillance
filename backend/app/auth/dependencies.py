from fastapi import Depends, HTTPException, status, Cookie
from jose import jwt, JWTError
from ..config import settings
from .models import User
from ..db.base import SessionLocal

def get_current_user(access_token: str = Cookie(None)):
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(
            access_token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        username = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
