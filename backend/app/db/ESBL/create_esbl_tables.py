# backend/app/db/ESBL/create_esbl_tables.py
from ..base import engine, Base
from .models_esbl import EsblIsolate, EsblAST, EsblFeatures, EsblPrediction

def main():
    Base.metadata.create_all(bind=engine, tables=[
        EsblIsolate.__table__,
        EsblAST.__table__,
        EsblFeatures.__table__,
        EsblPrediction.__table__,
    ])
    print("✅ ESBL tables created/verified.")

if __name__ == "__main__":
    main()

