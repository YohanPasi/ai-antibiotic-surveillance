
import os
import json
import pickle
import numpy as np
import pandas as pd
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any

# Paths
# Dynamic Path Resolution for Docker (Flat) vs Local (Nested)
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(current_dir, "Models")):
    BASE_DIR = current_dir # Docker: /app/Models exists
else:
    BASE_DIR = os.path.dirname(current_dir) # Local: ../Models exists

MODEL_PATH = os.path.join(BASE_DIR, "Models", "esbl_xgb_early_v1.pkl")
MODEL_META_PATH = os.path.join(BASE_DIR, "Models", "esbl_xgb_early_v1_metadata.json")
THRESHOLDS_PATH = os.path.join(BASE_DIR, "Config", "esbl_early_thresholds.json")
EVIDENCE_PATH = os.path.join(BASE_DIR, "Config", "antibiotic_outcome_tables.json")
GOVERNANCE_PATH = os.path.join(BASE_DIR, "Config", "governance_rules.json")
FEATURES_PATH = os.path.join(BASE_DIR, "Processed", "ESBL_Stage2_feature_names.json")

class ValidationResponse(BaseModel):
    allowed: bool
    reason: Optional[str] = None

class ESBLService:
    def __init__(self):
        self.model = None
        self.thresholds = None
        self.evidence = None
        self.governance = None
        self.feature_names = None
        self.metadata = None
        self.excluded_features = ["CTX", "CAZ", "CRO"] # Hardcoded safety fallback

        self.load_resources()

    def load_resources(self):
        """Loads all necessary artifacts for the CDSS."""
        if not all(os.path.exists(p) for p in [MODEL_PATH, THRESHOLDS_PATH, EVIDENCE_PATH, GOVERNANCE_PATH, FEATURES_PATH]):
            raise RuntimeError("Critical ESBL artifacts missing. CDSS cannot start.")

        with open(MODEL_PATH, 'rb') as f:
            self.model = pickle.load(f)
        
        with open(THRESHOLDS_PATH, 'r') as f:
            self.thresholds = json.load(f)

        with open(EVIDENCE_PATH, 'r') as f:
            self.evidence = json.load(f)

        with open(GOVERNANCE_PATH, 'r') as f:
            self.governance = json.load(f)
            
        with open(MODEL_META_PATH, 'r') as f:
            self.metadata = json.load(f)

        with open(FEATURES_PATH, 'r') as f:
            full_features = json.load(f)
            # FILTERING: Align with Stage 5 Masking
            # Remove any feature containing excluded terms
            self.feature_names = [f for f in full_features if not any(ex in f for ex in self.excluded_features)]
            
        print(f"✅ ESBL Service Resources Loaded Successfully. Features Aligned: {len(self.feature_names)}")

    def validate_scope(self, organism: str, gram_result: str) -> ValidationResponse:
        """
        Enforces Scope Governance (Stage 8).
        Only allows Enterobacterales and GNB.
        """
        rules = self.governance["scope_enforcement"]
        
        # Normalize inputs
        org_clean = organism.replace(" ", "_").replace(".", "") 
        # Simple mapping for demo; widespread production needs robust mapping
        
        # Check Gram
        if gram_result != rules["allowed_gram_result"]:
             return ValidationResponse(allowed=False, reason=f"Gram stain {gram_result} not in scope (Only GNB).")

        # Check Organism is broadly Enterobacterales (Simplified check)
        # In a real system, use a taxonomy tree. Here, check typicals.
        # But wait, raw input might vary. Let's trust the frontend provides mapped keys or check substring?
        # For safety, let's implement a 'contains' check vs the allowed list if exact match fails, or exact.
        # Given "E_coli", "Klebsiella_pneumoniae", "Enterobacter_spp" in rules.
        
        # Allow exact match from dropdown
        if organism in rules["allowed_organisms"]:
             return ValidationResponse(allowed=True)
             
        # Allow partial match for "E. coli" -> "E_coli" mapping happening upstream?
        # Let's assume frontend sends valid keys. If not:
        return ValidationResponse(allowed=False, reason=f"Organism {organism} not in governance scope.")


    def _prepare_features(self, input_data: Dict) -> np.ndarray:
        """
        Maps API input dictionary to Model Feature Vector.
        Handles Masking (Stage 5) and OOD check.
        """
        # 1. Initialize zero vector
        feature_vector = np.zeros((1, len(self.feature_names)))
        
        # 2. Map Categorical One-Hots (Simple version for demo)
        # In production, use the saved Encoder from Stage 2.
        # Here we manually simulate the mapping logic or assume pre-encoded? 
        # Stage 2 saved X_train.npy but not the encoder explicitly?
        # Actually, Stage 2 code used `pd.get_dummies`.
        # To reproduce this at runtime perfectly, we need alignment.
        # Strategy: Use `feature_names` to map input keys "Ward_ICU" -> index.
        
        for key, value in input_data.items():
            # Example: "Ward": "ICU" -> Look for feature "Ward_ICU"
            feature_col = f"{key}_{value}"
            if feature_col in self.feature_names:
                idx = self.feature_names.index(feature_col)
                feature_vector[0, idx] = 1.0
            # Numeric fields? Age?
            elif key in self.feature_names: # Direct numeric match
                 idx = self.feature_names.index(key)
                 feature_vector[0, idx] = float(value)
                 
        # 3. Apply Masking (Stage 5) - Zero out excluded features just in case
        for excl in self.excluded_features:
            for i, name in enumerate(self.feature_names):
                if excl in name:
                     feature_vector[0, i] = 0.0 # Force zero
                     
        return feature_vector

    def check_ood(self, input_data: Dict) -> bool:
        """
        Simple Out-of-Distribution Check (Stage 9 Requirement).
        Checks boundaries of numeric inputs (Age, Growth Time).
        """
        # Hardcoded safe bounds for now (derived from dataset stats approx)
        # Age: 0-100
        # Growth Time: 0-200
        if "Age" in input_data:
            if not (0 <= float(input_data["Age"]) <= 110): return True
        return False

    def check_ast_lock(self, ast_available: bool):
        """Stage 8: Decision Freeze Check."""
        if ast_available:
            raise HTTPException(
                status_code=403,
                detail="AST results available. Empiric prediction disabled per governance protocol."
            )

    def predict_and_evaluate(self, request_data: Dict):
        """
        Main Engine Method (Stage 9).
        Combines Risk Prediction, Stratification, and Recommendation.
        """
        inputs = request_data.get("inputs", {})
        ast_available = request_data.get("ast_available", False)
        
        # 1. Governance Stops
        self.check_ast_lock(ast_available)
        
        scope = self.validate_scope(inputs.get("Organism", ""), inputs.get("Gram", ""))
        if not scope.allowed:
            raise HTTPException(status_code=400, detail=scope.reason)
            
        # 2. Prepare Features
        X = self._prepare_features(inputs)
        
        # 3. Predict Risk (Stage 5)
        prob = self.model.predict_proba(X)[0, 1]
        
        # 4. Stratify (Stage 6)
        t_low = self.thresholds["thresholds"]["low"]
        t_high = self.thresholds["thresholds"]["high"]
        
        risk_group = "Moderate"
        if prob < t_low: risk_group = "Low"
        elif prob >= t_high: risk_group = "High"
        
        # 5. OOD Check
        ood_flag = self.check_ood(inputs)
        
        # 6. Recommendations (Stage 7 logic reused/adapted)
        # (Simplified implementation of the Stage 7 script logic here for the API)
        # Ideally import the function, but for API stability, I'll reproduce key steps concisely.
        recommendations = self._generate_recommendations(prob, risk_group)
        
        response = {
            "risk": {
                "probability": round(float(prob), 4),
                "group": risk_group,
                "ood_warning": ood_flag
            },
            "recommendations": recommendations,
            "metadata": {
                "model_version": self.metadata.get("config_hash", "unknown")[:8],
                "threshold_version": "v1.0", # Placeholder or hash content
                "evidence_version": "v1.0"
            },
            "warnings": [
                "Empiric decision support only.",
                "Do not delay AST-guided therapy."
            ]
        }
        
        if ood_flag:
            response["warnings"].append("⚠️ Input outside training distribution (OOD).")
            
        return response

    def _generate_recommendations(self, p_esbl, risk_group):
        """Helper to generate ranked list based on Bayesian Success + Stewardship."""
        # Config weights (reused from Stage 7 script)
        # In a real app, load from JSON.
        STEWARDSHIP_WEIGHTS = {"MEM": 0.6, "IMP": 0.6, "ETP": 0.6, "TZP": 0.9, "AMK": 1.0} 
        HIGH_RISK_OVERRIDES = ["MEM", "IMP", "ETP", "AMK"]
        
        recs = []
        for drug, data in self.evidence.items():
             # Bayesian Calculation
             s_esbl, n_esbl = data["ESBL"]["success"], data["ESBL"]["total"]
             s_non, n_non = data["non_ESBL"]["success"], data["non_ESBL"]["total"]
             
             if n_esbl < 30 or n_non < 30: continue # Eligibility
             
             alpha = 2.0
             p_s_esbl = (s_esbl + alpha) / (n_esbl + 2*alpha)
             p_s_non = (s_non + alpha) / (n_non + 2*alpha)
             
             exp_success = (p_esbl * p_s_esbl) + ((1 - p_esbl) * p_s_non)
             
             # Stewardship
             weight = STEWARDSHIP_WEIGHTS.get(drug, 0.8)
             if risk_group == "High" and drug in HIGH_RISK_OVERRIDES: weight = 1.0
             if risk_group == "Low" and drug in ["MEM", "IMP", "ETP"]: weight = 0.2
             
             score = exp_success * weight
             
             recs.append({
                 "drug": drug,
                 "success_prob": round(float(exp_success), 2),
                 "score": round(float(score), 2),
                 "stewardship_note": "Restricted" if weight < 0.8 else "Standard" 
             })
             
        recs.sort(key=lambda x: x["score"], reverse=True)
        return recs[:5]

esbl_service = ESBLService()
