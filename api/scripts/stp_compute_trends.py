
import sys
import os
import pandas as pd
import numpy as np
from sqlalchemy import text
from scipy.stats import linregress

# Add /app to python path for Docker compatibility
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine

def compute_trends():
    print("Connecting to database...")
    db = SessionLocal()
    
    try:
        # 1. Fetch Weekly Rates
        print("Fetching weekly resistance rates...")
        query = text("""
            SELECT week_start, ward, organism, antibiotic, resistance_rate
            FROM stp_resistance_rates_weekly
            ORDER BY ward, organism, antibiotic, week_start
        """)
        
        df = pd.read_sql(query, db.bind)
        
        if df.empty:
            print("No data found in stp_resistance_rates_weekly.")
            return

        # Ensure date format
        df['week_start'] = pd.to_datetime(df['week_start'])
        
        # Convert week_start to numeric (ordinal) for regression
        df['week_ordinal'] = df['week_start'].map(pd.Timestamp.toordinal)

        results = []
        
        # 2. Group by Ward, Organism, Antibiotic
        grouped = df.groupby(['ward', 'organism', 'antibiotic'])
        
        print(f"Processing {len(grouped)} series for trend analysis...")
        
        for name, group in grouped:
            ward, organism, antibiotic = name
            
            # Minimum data points for trend
            if len(group) < 4:
                continue
                
            # Linear Regression
            slope, intercept, r_value, p_value, std_err = linregress(group['week_ordinal'], group['resistance_rate'])
            
            # Volatility (Standard Deviation of residuals or just raw rate std dev)
            volatility = group['resistance_rate'].std()
            
            results.append({
                'ward': ward,
                'organism': organism,
                'antibiotic': antibiotic,
                'week_start': group['week_start'].max(), # Anchor to latest date
                'rolling_slope': slope * 365, # Annualized slope (change per year)
                'volatility': volatility,
                # Extra internal metrics (not in DB)
                # 'p_value': p_value,
                # 'r_squared': r_value**2,
                # 'sample_size': len(group)
            })
            
        if not results:
            print("No valid trends computed.")
            return

        results_df = pd.DataFrame(results)
        
        # 3. Save to stp_temporal_trend_signals
        print(f"Saving {len(results_df)} signals to DB...")
        
        # Clear existing
        try:
            db.execute(text("DELETE FROM stp_temporal_trend_signals")) # DELETE avoids cascade issues
            db.commit()
        except:
            db.rollback()
        
        results_df.to_sql('stp_temporal_trend_signals', engine, if_exists='append', index=False)
        print("✅ Trend calculation complete.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    compute_trends()
