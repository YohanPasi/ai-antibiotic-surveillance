from ..db.base import SessionLocal, Base, engine
from .models import User
from .utils import hash_password

def create_admin():
    # Ensure User table exists
    Base.metadata.create_all(bind=engine, tables=[User.__table__])
    
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == "admin").first():
            print("Admin already exists.")
            return

        admin = User(
            username="admin",
            password_hash=hash_password("admin@123"),
            role="admin"
        )
        db.add(admin)
        db.commit()
        print("✅ Admin user created: admin / admin@123")
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
