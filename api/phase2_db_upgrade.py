from database import SessionLocal
from sqlalchemy import text
db = SessionLocal()
try:
    # 1. Rename column
    db.execute(text("ALTER TABLE ast_manual_entry RENAME COLUMN entry_date TO culture_date;"))
    db.commit()
    print('Renamed column successfully.')
except Exception as e:
    db.rollback()
    print('Rename failed or already done:', e)

try:
    # 2. Add future date constraint
    db.execute(text("ALTER TABLE ast_manual_entry ADD CONSTRAINT culture_date_not_future CHECK (culture_date <= CURRENT_DATE);"))
    db.commit()
    print('Added constraint successfully.')
except Exception as e:
    db.rollback()
    print('Constraint failed or already added:', e)

finally:
    db.close()
