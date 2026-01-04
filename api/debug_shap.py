import os
import joblib
import json
import pandas as pd
import shap
import sqlalchemy
from sqlalchemy import create_engine, text
from sklearn.ensemble import RandomForestClassifier

# Setup
DATABASE_URL = os.getenv("DATABASE_URL")
ARTIFACT_DIR = "/app/models/mrsa_artifacts"

print("--- DEBUG SHAP SCRIPT ---")

# 1. DB Connection
engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    # Fetch ID 2 (or latest)
    print("Fetching ID 2...")
    row = conn.execute(text("SELECT input_snapshot FROM mrsa_risk_assessments WHERE id = 2")).fetchone()
    if not row:
        print("ID 2 not found, trying ID 1...")
        row = conn.execute(text("SELECT input_snapshot FROM mrsa_risk_assessments WHERE id = 1")).fetchone()
    
    if not row:
        print("No records found!")
        exit(1)
        
    snapshot = row[0]
    print(f"Snapshot: {snapshot}")

# 2. Load Artifacts
print("Loading Artifacts...")
try:
    # Load separate components as mrsa_service does
    classifier = joblib.load(os.path.join(ARTIFACT_DIR, 'mrsa_rf_model.pkl'))
    preprocessor = joblib.load(os.path.join(ARTIFACT_DIR, 'mrsa_preprocessor.pkl'))
    print("Artifacts loaded.")
except Exception as e:
    print(f"Artifact Load Failed: {e}")
    exit(1)

# 3. Simulate Explain Logic
print("Running SHAP Logic...")
try:
    input_df = pd.DataFrame([snapshot])
    
    # Transform
    print("Transforming...")
    X_transformed = preprocessor.transform(input_df)
    print(f"Transformed Shape: {X_transformed.shape}")
    
    # SHAP
    print("Initializing Explainer...")
    explainer = shap.TreeExplainer(classifier)
    
    print("Calculating SHAP Values...")
    shap_values = explainer.shap_values(X_transformed, check_additivity=False)
    
    vals = shap_values[1][0]
    print("SHAP Success!")
    print(f"SHAP Values: {vals}")

except Exception as e:
    print("\n!!! CRASHED !!!")
    import traceback
    traceback.print_exc()
