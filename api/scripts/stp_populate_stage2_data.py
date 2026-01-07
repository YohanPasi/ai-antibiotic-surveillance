
import sys
import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Add /app to python path for Docker compatibility
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine
from analysis_engine.stp_compute_resistance_rates import aggregate_resistance_rates
from sqlalchemy import text
from datetime import datetime
import pandas as pd

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def populate_stage2_data():
    logger.info("Connecting to database...")
    db = SessionLocal()
    
    try:
        # 1. Clear Existing Data (Robustly)
        logger.info("Clearing existing Stage 2 data...")
        try:
            db.execute(text("DELETE FROM stp_resistance_rates_weekly"))
            db.execute(text("DELETE FROM stp_ward_resistance_profile"))
            db.commit()
        except Exception as e:
            logger.warning(f"Could not clear table cleanly. Proceeding to Insert... Error: {e}")
            db.rollback()

        # 2. Fetch Raw Validated AST Data (Real Data)
        logger.info("Fetching validated AST data from public.stp_canonical_long...")
        query = """
        SELECT organism, antibiotic, ward, sample_date, ast_result 
        FROM public.stp_canonical_long 
        WHERE ast_result IN ('S', 'I', 'R')
        """
        df = pd.read_sql(query, engine)
        
        if df.empty:
            logger.error("No data found in stp_canonical_long! Is the table empty?")
            return

        logger.info(f"Loaded {len(df)} records from Real DB.")

        # Ensure datetime
        df['collection_date'] = pd.to_datetime(df['sample_date'])
        
        # Create 'week_start' for aggregation
        df['week_start'] = df['collection_date'].dt.to_period('W').apply(lambda r: r.start_time)

        # -----------------------------------------------------
        # 3. Compute Weekly Resistance Rates
        # -----------------------------------------------------
        logger.info("Computing Weekly Resistance Rates...")
        weekly_metrics = aggregate_resistance_rates(
            df, 
            group_cols=['organism', 'antibiotic', 'ward', 'week_start'],
            min_threshold=5 
        )
        
        logger.info(f"Computed {len(weekly_metrics)} weekly metric rows.")
        
        # Save to DB (stp_resistance_rates_weekly)
        logger.info("Saving to stp_resistance_rates_weekly...")
        weekly_metrics.to_sql(
            'stp_resistance_rates_weekly', 
            engine, 
            if_exists='append', 
            index=False,
            method='multi',
            chunksize=500
        )

        # -----------------------------------------------------
        # 4. Compute Ward Resistance Profiles (Overall)
        # -----------------------------------------------------
        logger.info("Computing Ward Resistance Profiles...")
        
        profile_metrics = aggregate_resistance_rates(
            df,
            group_cols=['ward', 'organism', 'antibiotic'],
            min_threshold=5
        )
        
        # Map columns to schema: 
        # resistance_rate -> mean_resistance
        # Needs std_resistance (0 for now), coverage (1.0), updated_at
        profile_metrics.rename(columns={'resistance_rate': 'mean_resistance'}, inplace=True)
        profile_metrics['std_resistance'] = 0.0
        profile_metrics['coverage_percent'] = 100.0
        profile_metrics['updated_at'] = datetime.now()
        
        # Drop columns not in target table if any (e.g. suppression_reason might not be there? Check schema)
        # Target table: ward, organism, antibiotic, mean_resistance, std_resistance, coverage_percent, observation_window_start, observation_window_end, updated_at
        # aggregate_resistance_rates returns: tested_count, susceptible..., is_stable, suppression_reason
        
        # We need to keep only valid columns for stp_ward_resistance_profile
        valid_cols = [
            'ward', 'organism', 'antibiotic', 
            'mean_resistance', 'std_resistance', 'coverage_percent', 
            'updated_at'
        ]
        
        # Filter columns
        profile_save_df = profile_metrics[valid_cols] if set(valid_cols).issubset(profile_metrics.columns) else profile_metrics
        
        logger.info(f"Computed {len(profile_save_df)} profile rows.")
        
        logger.info("Saving to stp_ward_resistance_profile...")
        profile_save_df.to_sql(
            'stp_ward_resistance_profile',
            engine,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=500
        )
        
        logger.info("✅ REAL DATA PIPELINE COMPLETE.")
        
    except Exception as e:
        logger.error(f"Failed to populate Stage 2 data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    populate_stage2_data()
