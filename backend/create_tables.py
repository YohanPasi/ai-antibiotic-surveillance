from app.db.base import Base, engine
from app.db import models

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("DONE!")
