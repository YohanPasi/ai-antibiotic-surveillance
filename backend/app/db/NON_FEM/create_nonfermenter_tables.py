from .base import Base, engine
from .models_nonfermenter import (
    NonFermenterIsolate,
    NonFermenterAST,
    NonFermenterFeature
)

def create_nonfermenter_tables():
    print("Creating Non-fermenter tables...")
    Base.metadata.create_all(bind=engine)
    print("Non-fermenter tables created successfully.")

if __name__ == "__main__":
    create_nonfermenter_tables()