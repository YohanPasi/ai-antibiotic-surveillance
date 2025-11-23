from .base import Base, engine
from .models_strep import StrepIsolate, StrepAST

def create_strep_tables():
    print("Creating STREP tables...")
    Base.metadata.create_all(bind=engine, tables=[
        StrepIsolate.__table__,
        StrepAST.__table__,
    ])
    print("✅ STREP tables created/verified.")

if __name__ == "__main__":
    create_strep_tables()

