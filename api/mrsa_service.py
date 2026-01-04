import pandas as pd
import numpy as np
import joblib
import json
import shap
import os
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import HTTPException
from mrsa_schemas import MRSAPredictionRequest, MRSAPredictionResponse, MRSAExplanationResponse
from datetime import datetime

ARTIFACT_DIR = r'/app/models/mrsa_artifacts' if os.path.exists('/app/models/mrsa_artifacts') else r'd:\Yohan\Project\api\models\mrsa_artifacts'

class MRSAService:
    def __init__(self):
        self.pipeline = None
        self.feature_columns = None
        self.model_version = "RF_v1"
        self._load_artifacts()

    def _load_artifacts(self):
        print(f"Loading MRSA Artifacts from {ARTIFACT_DIR}...")
        try:
            self.pipeline = joblib.load(os.path.join(ARTIFACT_DIR, 'mrsa_rf_pipeline.pkl'))
            with open(os.path.join(ARTIFACT_DIR, 'feature_columns.json'), 'r') as f:
                self.feature_columns = json.load(f)
            
            # Pre-compute SHAP explainer (Background dataset for expected value)
            # Using specific tree explainer on the classifier part
            # Note: For strict exactness we iterate, but for speed we cache
            self.classifier = self.pipeline.named_steps['classifier']
            self.preprocessor = self.pipeline.named_steps['preprocessor']
            
            print("✅ MRSA Service Ready.")
        except Exception as e:
            print(f"❌ Failed to load MRSA artifacts: {e}")
            self.pipeline = None

    def predict(self, db: Session, request: MRSAPredictionRequest) -> MRSAPredictionResponse:
        # 1. Runtime Isolation Guard
        forbidden = ["forecast", "antibiotic", "week", "future"]
        req_dict = request.dict()
        if any(k in req_dict for k in forbidden):
             raise HTTPException(status_code=400, detail="Security Rejection: Forbidden forecasting fields detected.")

        # 2. DataFrame Construction
        input_data = pd.DataFrame([req_dict])
        
        # 3. Consensus Prediction (Delegated)
        try:
            from mrsa_consensus_service import consensus_service
            # This handles prediction, logic, and auditing
            result = consensus_service.predict_consensus(input_data)
            
            # Extract Core Values for compatibility
            # We use RF probability as the "Primary Probability" for continuity
            prob = result['models']['rf']['prob']
            
            # But the RISK BAND is the CONSENSUS BAND
            band = result['consensus_band']
            
            # Message logic based on Consensus Band & Confidence
            confidence = result['confidence_level']
            
            if band == "GREEN":
                msg = "MRSA unlikely. Standard empiric therapy."
            elif band == "AMBER":
                msg = "Intermediate Risk. Review risk factors."
            else:
                msg = "High Risk. Consider anti-MRSA coverage."
                
            if confidence != "HIGH":
                msg += f" (Note: Confidence is {confidence} due to model disagreement)"

            # We need the ID from the DB. Consensus service did the inert, but we need to fetch the ID?
            # Actually consensus_service.predict_consensus accepts an ID if we want to update.
            # But we need to CREATE the record first or let consensus service create it?
            # The previous logic created it.
            # Let's let consensus service CREATE it.
            # Wait, my previous implementation of predict_consensus UPDATEs if ID provided.
            # I need to Create first.
            
            # Creating Audit Record Initial Placeholder
            sql = text("""
                INSERT INTO mrsa_risk_assessments 
                (ward, sample_type, mrsa_probability, risk_band, model_version, input_snapshot)
                VALUES (:ward, :sample, :prob, :band, :ver, :snap)
                RETURNING id
            """)
            audit_res = db.execute(sql, {
                "ward": request.ward,
                "sample": request.sample_type,
                "prob": prob,
                "band": band,
                "ver": "C5_Consensus",
                "snap": json.dumps(req_dict)
            })
            db.commit()
            assessment_id = audit_res.fetchone()[0]
            
            # Now Update with Full Consensus Details
            consensus_service.predict_consensus(input_data, assessment_id=assessment_id)
            
        except Exception as e:
            db.rollback()
            # Fallback to simple RF if consensus fails? No, fail hard for safety.
            print(f"Prediction/Consensus Failed: {e}")
            raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

        return MRSAPredictionResponse(
            assessment_id=assessment_id,
            mrsa_probability=prob,
            risk_band=band,
            stewardship_message=msg,
            model_version=result['consensus_version'],
            input_snapshot=req_dict,
            consensus_details=result
        )

    def explain(self, db: Session, assessment_id: int) -> MRSAExplanationResponse:
        # 1. Fetch Snapshot (Guaranteed consistency)
        sql = text("SELECT input_snapshot, risk_band FROM mrsa_risk_assessments WHERE id = :id")
        result = db.execute(sql, {"id": assessment_id}).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Assessment not found.")
            
        snapshot = result[0]
        risk_band = result[1]
        
        # 2. Transform Input using Preprocessor
        input_df = pd.DataFrame([snapshot])
        try:
            X_transformed = self.preprocessor.transform(input_df)
            
            # 3. Calculate SHAP
            # For RF, TreeExplainer is best. 
            explainer = shap.TreeExplainer(self.classifier)
            # check_additivity=False because of approximate float precision in sklearn pipeline
            shap_values = explainer.shap_values(X_transformed, check_additivity=False)
            
            # Debug Log
            print(f"DEBUG: SHAP type={type(shap_values)}")
            if isinstance(shap_values, list):
                 print(f"DEBUG: SHAP list len={len(shap_values)} shape0={shap_values[0].shape}")
            elif hasattr(shap_values, 'shape'):
                 print(f"DEBUG: SHAP array shape={shap_values.shape}")

            # 4. Handle SHAP return structure
            # Logic: We want a 1D array of feature contributions for the SINGLE sample we predicted
            if isinstance(shap_values, list):
                if len(shap_values) >= 2:
                     # List of arrays? 
                     # If shap_values[1] is (1, N), we want index 0
                     temp = shap_values[1]
                else:
                     temp = shap_values[0]
            else:
                temp = shap_values

            # Handle Dimensions
            # Target: (N_features,) 1D array
            if len(temp.shape) == 3: 
                # (Samples, Features, Classes) e.g. (1, 20, 2)
                # We want Sample 0, All Features, Class 1
                vals = temp[0, :, 1]
            elif len(temp.shape) == 2:
                # (Samples, Features) e.g. (1, 20) OR (Features, Classes)? Usually (1, 20)
                # If N_feat=20
                if temp.shape[0] == 1:
                    vals = temp[0] 
                else: 
                     # Suspicious but maybe it is (20, 2)? No, shap usually (Samples, Feats)
                     vals = temp[0] 
            else:
                 vals = temp

            print(f"DEBUG: Final vals shape={vals.shape}")

        except Exception as e:
            print(f"SHAP Calculation Error: {e}") 
            raise HTTPException(status_code=500, detail=f"Explanation computation failed: {str(e)}")

        # 4. Map back to feature names
        try:
            # Restore Missing Code
            ohe_cats = self.preprocessor.named_transformers_['cat'].get_feature_names_out()
            nums = ['age', 'growth_time'] 
            all_feats = list(nums) + list(ohe_cats) + ['cell_count']
            
            print(f"DEBUG: all_feats ({len(all_feats)}): {all_feats}", flush=True)
            print(f"DEBUG: vals ({len(vals)})", flush=True)

            explanations = []
            # Ensure proper iteration
            if len(vals) != len(all_feats):
                print(f"WARNING: Feature count mismatch! Feats={len(all_feats)}, SHAP={len(vals)}")
            
            for name, impact in zip(all_feats, vals):
                if isinstance(impact, (list, np.ndarray)):
                     try:
                        impact = float(impact) 
                     except:
                        impact = float(impact[0]) 

                # FILTERING LOGIC: Only show relevant/active features
                # 1. Minimum Impact Filter
                if abs(impact) < 0.015: 
                    continue

                # 2. Domain Specific: Hide Pus Type if Sample is NOT Pus/Wound
                # "Pus Type" is only relevant for Pus samples. "Unknown" appears otherwise, which is confusing.
                if "pus_type" in name.lower():
                     sample_val = str(input_df.iloc[0].get("sample_type", "")).lower()
                     if "pus" not in sample_val and "wound" not in sample_val:
                         continue

                # 3. Inactive Category Filter
                # Note: Feature names are like 'ward_ICU', 'sample_type_Blood' (No cat__ prefix)
                found_col = None
                known_cols = ['ward', 'sample_type', 'pus_type', 'gram_positivity', 'gender']
                
                for col in known_cols:
                        # Check strictly for "colname_" to avoid partial matches
                        # e.g. "ward_" matches "ward_ICU"
                        prefix = f"{col}_"
                        if name.startswith(prefix):
                            found_col = col
                            break
                
                if found_col:
                    # Extract the value part from the feature name
                    # e.g. ward_ICU -> ICU
                    feature_val_suffix = name.replace(f"{found_col}_", "")
                    
                    # Get actual input value
                    actual_val = str(input_df.iloc[0].get(found_col, ""))
                    
                    # Normalizing comparison (Case insensitive stripping)
                    if actual_val.lower().strip() != feature_val_suffix.lower().strip():
                        # Double check for spaces/underscores (e.g. "Ward 01" vs "Ward_01")
                        suffix_clean = feature_val_suffix.replace("_", " ").lower().strip()
                        actual_clean = actual_val.replace("_", " ").lower().strip()
                        
                        if actual_clean != suffix_clean:
                            continue

                clean_name = name.replace("cat__", "").replace("remainder__", "").replace("_", " ").title()
                # Safe get for display value
                display_val = ""
                # Try to find which original column this feature belongs to for display
                for col in ['age', 'growth_time', 'cell_count', 'ward', 'sample_type', 'pus_type', 'gram_positivity', 'gender']:
                    if col in name.lower():
                        display_val = str(input_df.iloc[0].get(col, ""))
                        break
                
                explanations.append({
                    "feature": clean_name,
                    "impact": float(impact),
                    "value": display_val
                })
            
            explanations.sort(key=lambda x: abs(x['impact']), reverse=True)
            
            return MRSAExplanationResponse(
                assessment_id=assessment_id,
                risk_band=risk_band,
                explanations=explanations[:10] # Top 10
            )
            
        except Exception as e:
            print(f"Feature mapping failed: {e}")
            raise HTTPException(status_code=500, detail="Could not map explanations.")

mrsa_service = MRSAService()
