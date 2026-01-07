
import sys
import os
from sqlalchemy import text
from datetime import date

# Add /app to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal

def get_date_range():
    db = SessionLocal()
    try:
        query = text('SELECT MIN(sample_date), MAX(sample_date) FROM public.stp_canonical_long')
        result = db.execute(query).fetchone()
        
        min_date = result[0]
        max_date = result[1]
        
        print(f"DATE_RANGE: {min_date} to {max_date}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    get_date_range()
