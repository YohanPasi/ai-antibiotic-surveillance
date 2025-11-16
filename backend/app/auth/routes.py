from fastapi import APIRouter, HTTPException, Response, status, Depends, Header
from sqlalchemy.orm import Session
from ..db.base import SessionLocal, Base, engine
from .models import User
from .utils import verify_password, hash_password, create_access_token
from .dependencies import get_current_user
from jose import jwt, JWTError
from ..config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login(data: dict, response: Response, db: Session = Depends(get_db)):
    username = data.get("username")
    password = data.get("password")

    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid username or password")

    token = create_access_token({"sub": user.username})

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,   # Set True in production
        samesite="Lax",
        max_age=3600
    )

    return {
        "user": {
            "username": user.username,
            "role": user.role,
            "id": user.id
        },
        "access_token": token
    }

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}

@router.post("/register")
def register(data: dict, db: Session = Depends(get_db)):
    username = data.get("username")
    password = data.get("password")
    full_name = data.get("full_name", "")

    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password are required")

    # Check if user already exists
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Create new user
    user = User(
        username=username,
        password_hash=hash_password(password),
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User created successfully", "username": user.username}

@router.get("/verify")
def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        return {"valid": False}

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        username = payload.get("sub")

        db = SessionLocal()
        user = db.query(User).filter(User.username == username).first()
        db.close()

        if not user:
            return {"valid": False}

        return {
            "valid": True,
            "user": {
                "username": user.username,
                "role": user.role,
                "id": user.id
            }
        }
    except JWTError:
        return {"valid": False}

@router.get("/me")
def get_me(user = Depends(get_current_user)):
    return {"username": user.username, "role": user.role}
