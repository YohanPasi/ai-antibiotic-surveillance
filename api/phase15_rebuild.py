"""
Phase 1.5 - Full Database Rebuild Script
Truncates aggregated/sweep tables, reruns Stage B, then triggers sweep.
"""
from database import SessionLocal
from sqlalchemy import text
from data_processor.aggregate_weekly import aggregate_weekly_data
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("phase15_rebuild")

db = SessionLocal()
try:
    logger.info("Truncating ast_weekly_aggregated...")
    db.execute(text("TRUNCATE ast_weekly_aggregated RESTART IDENTITY CASCADE"))
    
    logger.info("Truncating surveillance_logs...")
    db.execute(text("TRUNCATE surveillance_logs RESTART IDENTITY CASCADE"))
    
    db.commit()
    logger.info("Tables truncated successfully.")
except Exception as e:
    db.rollback()
    logger.error(f"Truncation error: {e}")
    raise
finally:
    db.close()

logger.info("Running Stage B Aggregation...")
agg_ok = aggregate_weekly_data()
logger.info(f"Stage B success: {agg_ok}")

if agg_ok:
    print("Done! Now run the admin sweep API endpoint.")
else:
    print("Stage B failed!")
