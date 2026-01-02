import joblib
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

class MRSAPredictor:
    def __init__(self, artifact_dir="/app/models/mrsa_artifacts"):
        self.artifact_dir = artifact_dir
        self.model = None
        self.scaler = None
        self.model_version = "XGB_v1"
        self.loaded = False
        
    def load_artifacts(self):
        """Loads model and scaler from disk."""
        try:
            print(f"🔄 Loading MRSA artifacts from {self.artifact_dir}...")
            self.model = joblib.load(os.path.join(self.artifact_dir, "mrsa_xgb_model.pkl"))
            self.scaler = joblib.load(os.path.join(self.artifact_dir, "scaler.pkl"))
            # We also might need feature columns if we want to be strict, but for now we'll reconstruct in order
            self.loaded = True
            print("✅ MRSA Model loaded successfully.")
        except Exception as e:
            print(f"❌ Failed to load MRSA model: {e}")
            self.loaded = False

    def predict(self, features: dict):
        """
        Predicts MRSA risk based on input features.
        Returns dict with probability, risk_band, and message.
        """
        if not self.loaded:
            self.load_artifacts()
            if not self.loaded:
                return {"error": "Model not loaded"}

        # 1. Preprocess Input
        # Create DataFrame from input dict (single row)
        input_df = pd.DataFrame([features])
        
        # A. Handle Categoricals & Missing (Simple imputation or defaults)
        # Assuming input is validated by Pydantic before this, but let's be safe
        
        # B. Encoding
        # Cell Count Ordinal Map
        cell_count_raw = str(features.get('cell_count', '0')).lower().strip()
        cell_map = {
            'none': 0, 'no wc': 0, 'not seen': 0, '0': 0,
            'rare': 1, '+': 1, 'scanty': 1,
            'few': 2, '++': 2,
            'moderate': 3, '+++': 3,
            'many': 4, 'plenty': 4, '++++': 4,
            'unknown': 0
        }
        cell_count_encoded = cell_map.get(cell_count_raw, 0)
        
        # One-Hot Encoding (Manual reconstruction to match training columns)
        # The model expects specific columns. We need to recreate the exact feature vector.
        # This is tricky without the saved feature list.
        # Let's load the feature list.
        try:
            with open(os.path.join(self.artifact_dir, "feature_columns.json"), "r") as f:
                model_columns = json.load(f)
        except Exception as e:
            return {"error": "Feature columns definition missing"}

        # Prepare a base dict with 0s for all model columns
        processed_data = {col: 0 for col in model_columns}
        
        # Fill Numeric
        processed_data['age'] = float(features.get('age', 0))
        processed_data['growth_time'] = float(features.get('growth_time', 0))
        processed_data['cell_count_encoded'] = float(cell_count_encoded)
        
        # Fill Categorical (One-Hot)
        # e.g. 'ward_ICU' -> 1
        ward = features.get('ward', 'Unknown')
        gender = features.get('gender', 'Unknown')
        sample = features.get('sample_type', 'Unknown')
        pus = features.get('pus_type', 'Unknown')
        gram = features.get('gram_positivity', 'Unknown')
        
        # Helper to set bit
        def set_bit(prefix, value):
             col_name = f"{prefix}_{value}"
             if col_name in processed_data:
                 processed_data[col_name] = 1
        
        set_bit('ward', ward)
        set_bit('gender', gender)
        set_bit('sample_type', sample)
        set_bit('pus_type', pus)
        set_bit('gram_positivity', gram)
        
        # Convert to DataFrame in correct order
        X_final = pd.DataFrame([processed_data], columns=model_columns)
        
        # C. Scaling (Numeric only)
        num_cols = ['age', 'growth_time', 'cell_count_encoded']
        X_final[num_cols] = self.scaler.transform(X_final[num_cols])
        
        # 2. Predict
        prob = float(self.model.predict_proba(X_final)[0][1])
        
        # 3. Threshold Logic
        if prob >= 0.60:
            risk = "RED"
            msg = "High MRSA risk. Initiate MRSA-active therapy."
        elif prob >= 0.30:
            risk = "AMBER"
            msg = "Intermediate MRSA risk. Review empirical choice."
        else:
            risk = "GREEN"
            msg = "Low MRSA risk. Standard therapy acceptable."
            
        return {
            "mrsa_probability": round(prob, 4),
            "risk_band": risk,
            "message": msg,
            "model_version": self.model_version,
            "timestamp": datetime.now().isoformat()
        }

    def validate_prediction(self, db_session, entry_data):
        """
        Stage D: Post-AST Validation.
        Triggered when AST results are saved.
        Checks for Staph Aureus + Cefoxitin (FOX) and validates against previous prediction.
        """
        # 1. Filter Scope (Staphylococcus aureus only)
        # Handle case-insensitive check
        org = str(entry_data.organism).lower()
        if "staph" not in org or "aureus" not in org:
            return # Not in scope
            
        # 2. Check for Cefoxitin (FOX) Result
        fox_result = None
        for res in entry_data.results:
            if "cefoxitin" in str(res.antibiotic).lower() or "fox" in str(res.antibiotic).lower():
                fox_result = res.result # 'S', 'I', 'R'
                break
        
        if not fox_result:
            return # No ground truth
            
        # 3. Define Ground Truth
        # simple rule: R -> MRSA (True), S -> MSSA (False) (Ignoring I for now or treating as R)
        actual_mrsa = (fox_result.upper() == 'R')
        
        # 4. Find Matching Prediction
        # Heuristic: Find most recent prediction for this Ward + Same Sample Type
        # In a real system, we'd use Patient ID / Visit ID.
        from sqlalchemy import text
        try:
            query = text("""
                SELECT id, predicted_probability, risk_band, model_version
                FROM mrsa_risk_assessments
                WHERE ward = :ward AND sample_type = :sample
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            # Map simplified sample types if needed (e.g. "Blood Culture" -> "Blood")
            # For now usage exact match or simple mapping
            sample_type = entry_data.specimen_type
            
            pred_row = db_session.execute(query, {
                "ward": entry_data.ward, 
                "sample": sample_type
            }).fetchone()
            
            if not pred_row:
                print(f"⚠️ Validation Skipped: No prior prediction found for {entry_data.ward}/{sample_type}")
                return

            pred_id = pred_row[0]
            prob = pred_row[1]
            risk_band = pred_row[2]
            version = pred_row[3]
            
            # 5. Determine Prediction (RED = MRSA)
            predicted_mrsa = (prob >= 0.60)
            
            # 6. Compare
            is_correct = (actual_mrsa == predicted_mrsa)
            
            # 7. Log Validation
            log_query = text("""
                INSERT INTO mrsa_validation_log
                (prediction_id, ward, predicted_probability, predicted_risk_band, 
                 actual_mrsa, prediction_correct, model_version)
                VALUES (:pid, :ward, :prob, :band, :actual, :correct, :ver)
            """)
            
            db_session.execute(log_query, {
                "pid": pred_id,
                "ward": entry_data.ward,
                "prob": prob,
                "band": risk_band,
                "actual": actual_mrsa,
                "correct": is_correct,
                "ver": version
            })
            db_session.commit()
            print(f"✅ MRSA Validation Logged: Actual={actual_mrsa}, Pred={predicted_mrsa}, Correct={is_correct}")
            
        except Exception as e:
            print(f"❌ Validation Error: {e}")

    def explain_prediction(self, db_session, assessment_id: int):
        """
        Stage F: Explainability Layer (The 'Why').
        Generates feature attribution using SHAP TreeExplainer for the given assessment.
        """
        import shap
        import pandas as pd
        import json
        import json
        from sqlalchemy import text
        
        # Ensure model is checked/loaded
        if not self.loaded:
            self.load_artifacts()
            if not self.loaded:
                return {"error": "Model not loaded"}
        
        # 1. Fetch Assessment Data
        query = text("SELECT clinical_features, model_version FROM mrsa_risk_assessments WHERE id = :id")
        row = db_session.execute(query, {"id": assessment_id}).fetchone()
        
        if not row:
            return {"error": "Assessment not found"}
            
        features_json = row[0]
        model_version = row[1]
        
        # Check if already a dict (SQLAlchemy JSON/JSONB auto-conversion)
        if isinstance(features_json, dict):
            input_data = features_json
        else:
            input_data = json.loads(features_json)
        
        # 2. Preprocess Input (Recreate X vector)
        # Note: We must replicate the EXACT dataframe structure used in training
        # For efficiency, we reuse the internal helper if possible, or reconstruct manually
        # Here we reconstruct manually carefully mapping to what 'predict' does
        
        # ... (Reusing logic from predict to build dataframe)
        # Ideally refactor 'predict' to return processed X, but for now we rebuild:
        df = pd.DataFrame([input_data])
        
        # Fill NA (same as training)
        df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(50) # median approx
        df['growth_time'] = pd.to_numeric(df['growth_time'], errors='coerce').fillna(24) # median
        
        # Encoding
        if 'cell_count' in df.columns:
            cell_map = {'none':0, 'no wc':0, 'not seen':0, '0':0, 'rare':1, '+':1, 'scanty':1, 'few':2, '++':2, 'moderate':3, '+++':3, 'many':4, 'plenty':4, '++++':4, 'unknown':0}
            df['cell_count_encoded'] = df['cell_count'].astype(str).str.lower().str.strip().map(cell_map).fillna(0)
            df = df.drop(columns=['cell_count'])
        else:
            df['cell_count_encoded'] = 0
            
        # One Hot (Need to match training columns exactly)
        # Load feature columns from artifact
        try:
            with open(os.path.join(self.artifact_dir, "feature_columns.json"), "r") as f:
                model_cols = json.load(f)
        except:
            return {"error": "Feature definition not found"}
            
        # Create dummies
        cat_cols = ['ward', 'gender', 'sample_type', 'pus_type', 'gram_positivity']
        for c in cat_cols:
            if c not in df.columns: df[c] = 'Unknown'
            
        df_encoded = pd.get_dummies(df, columns=[c for c in cat_cols if c in df.columns], drop_first=True)
        
        # Align columns
        for col in model_cols:
            if col not in df_encoded.columns:
                df_encoded[col] = 0
        df_final = df_encoded[model_cols]
        
        # Scale (using loaded scaler)
        num_cols = ['age', 'growth_time', 'cell_count_encoded']
        df_final[num_cols] = self.scaler.transform(df_final[num_cols])
        
        # 3. Calculate SHAP Values
        # TreeExplainer is efficient for RF/XGB
        explainer = shap.TreeExplainer(self.model)
        shap_values = explainer.shap_values(df_final)
        
        # For Classification, shap_values is list [class0, class1]. We want class1 (MRSA=True)
        # Random Forest shap_values might be array (n_samples, n_features, n_classes) or list
        if isinstance(shap_values, list):
            # Class 1 is usually index 1
            vals = shap_values[1][0] 
        else:
            # If standard array (binary)
            if len(shap_values.shape) == 3:
                vals = shap_values[0, :, 1]
            else:
                 vals = shap_values[0] # Fallback
                 
        # 4. Rank Features
        explanation_list = []
        feature_names = df_final.columns
        
        for i, val in enumerate(vals):
            if abs(val) > 0.001: # Filter tiny contributions
                direction = "increase" if val > 0 else "decrease"
                explanation_list.append({
                    "feature": feature_names[i],
                    "contribution": float(val),
                    "direction": direction,
                    "impact_score": abs(float(val))
                })
        
        # Sort by impact
        explanation_list.sort(key=lambda x: x['impact_score'], reverse=True)
        top_features = explanation_list[:5] # Top 5
        
        # 5. Persist to DB
        # Check if already exists? (Optional, but good explanation is unchanging)
        # For now, we insert.
        ins_query = text("""
            INSERT INTO mrsa_explanations (assessment_id, feature, contribution, direction, model_version)
            VALUES (:aid, :feat, :cont, :dir, :ver)
        """)
        
        for item in top_features:
            db_session.execute(ins_query, {
                "aid": assessment_id,
                "feat": item["feature"],
                "cont": item["contribution"],
                "dir": item["direction"],
                "ver": model_version
            })
        db_session.commit()
        
        return {
            "assessment_id": assessment_id,
            "explanations": top_features
        }

# Global Instance
predictor = MRSAPredictor()
