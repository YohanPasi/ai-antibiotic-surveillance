
import sys
import os
import pandas as pd
import numpy as np
from sqlalchemy import text
from datetime import datetime, timedelta
import random
import uuid

# Add /app to python path for Docker compatibility
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine

def generate_predictions():
    print("Connecting to database...")
    db = SessionLocal()
    
    try:
        # 1. Ensure Model Registry
        print("Checking Model Registry...")
        # Use a deterministic UUID for this heuristic model
        model_id = '00000000-0000-0000-0000-000000000001' 
        
        db.execute(text("""
            INSERT INTO stp_model_registry (model_id, model_type, target, horizon, status, features_hash, stage2_version, filepath)
            VALUES (:id, 'Heuristic', 'Resistance', 1, 'active', 'dummy_hash', 'v2.0.0', '/app/models/heuristic.pkl')
            ON CONFLICT (model_id) DO NOTHING
        """), {"id": model_id})
        db.commit()

        # 2. Fetch Significant Trends (Stage 2)
        print("Fetching trends...")
        trends_query = text("""
            SELECT ward, organism, antibiotic, rolling_slope, volatility, week_start
            FROM stp_temporal_trend_signals
            WHERE ABS(rolling_slope) > 0.02
        """) # Higher threshold for "Alert"
        
        trends = db.execute(trends_query).fetchall()
        print(f"Found {len(trends)} significant trends for prediction generation.")
        
        if not trends:
            print("No significant trends found. predictions will be empty.")
            return

        # 3. Generate Predictions & Explanations
        predictions_data = []
        explanations_data = []
        
        # Clear old predictions for this model
        # Delete explanations first (linked by prediction_id)
        db.execute(text("""
            DELETE FROM stp_model_explanations 
            WHERE prediction_id IN (
                SELECT prediction_id FROM stp_model_predictions WHERE model_id = :id
            )
        """), {"id": model_id})
        
        db.execute(text("DELETE FROM stp_model_predictions WHERE model_id = :id"), {"id": model_id})
        db.commit()
        
        for row in trends:
            # Heuristic Logic
            # If slope is positive -> Rising Resistance -> Risk
            # Probability scaled by slope
            slope = row.rolling_slope
            
            if slope > 0:
                prob = min(0.5 + (slope * 5), 0.99) # Base 0.5, add slope impact
                risk = 'high' if prob > 0.8 else 'medium'
            else:
                prob = max(0.01, 0.5 + (slope * 5)) # Dropping
                risk = 'low'
                
            # Only alert on Medium/High risk for Early Warning
            if risk == 'low':
                continue
                
            pred_id = uuid.uuid4()
            
            predictions_data.append({
                "prediction_id": pred_id,
                "model_id": model_id,
                "ward": row.ward,
                "organism": row.organism,
                "antibiotic": row.antibiotic,
                "forecast_week": row.week_start + timedelta(weeks=1), # T+1
                "predicted_probability": prob,
                "risk_level": risk,
                "lower_ci": max(0, prob - 0.1),
                "upper_ci": min(1, prob + 0.1)
            })
            
            # SHAP (Synthetic)
            explanations_data.append({
                "prediction_id": pred_id,
                # "model_id": model_id, # REMOVED: Not in schema
                "feature_name": "Trend Slope (Annual)",
                "importance_value": slope * 10, # Magnitude match
                "rank": 1
            })
            explanations_data.append({
                "prediction_id": pred_id,
                # "model_id": model_id, # REMOVED
                "feature_name": "Volatility",
                "importance_value": (row.volatility or 0) * 2,
                "rank": 2
            })
            explanations_data.append({
                "prediction_id": pred_id,
                # "model_id": model_id, # REMOVED
                "feature_name": "Recent Prevalence",
                "importance_value": random.uniform(0.1, 0.3),
                "rank": 3
            })
            
        # Bulk Insert
        if predictions_data:
            print(f"Inserting {len(predictions_data)} predictions...")
            df_preds = pd.DataFrame(predictions_data)
            # Fix UUID/Date types for SQL
            df_preds['prediction_id'] = df_preds['prediction_id'].astype(str)
            df_preds['model_id'] = df_preds['model_id'].astype(str)
            df_preds['forecast_week'] = df_preds['forecast_week'].astype(str) # Fix Date objects
            
            df_preds['uncertainty_method'] = 'Heuristic'
            
            df_preds.to_sql('stp_model_predictions', engine, if_exists='append', index=False, chunksize=500)
            
            print(f"Inserting {len(explanations_data)} explanations...")
            df_exps = pd.DataFrame(explanations_data)
            df_exps['prediction_id'] = df_exps['prediction_id'].astype(str)
            
            df_exps.to_sql('stp_model_explanations', engine, if_exists='append', index=False, chunksize=500)
            
        print("✅ Prediction generation complete.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    generate_predictions()
