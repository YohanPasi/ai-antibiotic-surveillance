# backend/app/db/create_mrsa_tables.py
from .base import engine, Base
from .models_mrsa import MrsaIsolate, MrsaAST, MrsaFeatures, MrsaPrediction

def main():
    Base.metadata.create_all(bind=engine, tables=[
        MrsaIsolate.__table__,
        MrsaAST.__table__,
        MrsaFeatures.__table__,
        MrsaPrediction.__table__,
    ])
    print("✅ MRSA tables created/verified.")

if __name__ == "__main__":
    main()
