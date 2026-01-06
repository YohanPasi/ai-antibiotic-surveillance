
import numpy as np
import pandas as pd
import json
import os
import sys
import pickle
from xgboost import XGBClassifier

# Constants
MODEL_PATH = "Models/esbl_xgb_early_v1.pkl"
THRESHOLDS_PATH = "Config/esbl_early_thresholds.json"
OUTCOME_TABLES_PATH = "Config/antibiotic_outcome_tables.json"
FEATURES_PATH = "Processed/ESBL_Stage2_feature_names.json"
EXCLUDED_FEATURES = ["CTX", "CAZ", "CRO"]

# Stewardship Configuration (Hardcoded for Research-Grade Logic)
# In production, this would be a config file.
STEWARDSHIP_WEIGHTS = {
    "MEM": 0.6,   # Meropenem: Reserve for High Risk
    "IMP": 0.6,   # Imipenem: Reserve
    "ETP": 0.6,   # Ertapenem: Reserve
    "TZP": 0.9,   # Pip-Tazo: Slight penalty, prefer narrower if possible
    "CIP": 0.8,   # Cipro: Penalty for collateral damage (C. diff)
    "LVX": 0.8,   # Levo: Penalty
    "GEN": 1.0,   # Gentamicin: Neutral
    "AMK": 1.0,   # Amikacin: Neutral
    "NIT": 1.0,   # Nitrofurantoin: Neutral (UTI only, assuming context)
    "SXT": 0.9,   # Bactrim: Slight penalty for resistance rates
    "AMC": 0.9,   # Augmentin: Standard
    "CXM": 0.8,   # Cefuroxime: Avoid in ESBL risk
    "CTX": 0.1,   # Ceftriaxone: HEAVY penalty if ESBL risk (Ineffective)
    "CAZ": 0.1,   # Ceftazidime: HEAVY penalty
    "CRO": 0.1,   # Ceftriaxone/Cefotaxime: HEAVY penalty
    "AMP": 0.5    # Ampicillin: High resistance likely, penalty
}

# Empirical "Bonus" Logic (Override Penalties for High Risk)
HIGH_RISK_OVERRIDES = ["MEM", "IMP", "ETP", "TZP", "AMK"] # These become 1.0 or boosted in High Risk

MIN_EVIDENCE_COUNT = 30 # Minimum N to consider an antibiotic "Reliable"

def load_resources():
    print("Loading Resources...")
    if not os.path.exists(MODEL_PATH) or not os.path.exists(THRESHOLDS_PATH) or not os.path.exists(OUTCOME_TABLES_PATH):
        print("❌ Missing artifacts. Run Stages 5, 6, 7-Generate first.")
        sys.exit(1)
        
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
        
    with open(THRESHOLDS_PATH, 'r') as f:
        thresholds = json.load(f)
        
    with open(OUTCOME_TABLES_PATH, 'r') as f:
        outcomes = json.load(f)
        
    with open(FEATURES_PATH, 'r') as f:
        feature_names = json.load(f)
        
    return model, thresholds, outcomes, feature_names

def apply_masking(X, feature_names):
    # Same masking logical as Stage 5/6
    keep_indices = []
    for i, name in enumerate(feature_names):
        if name not in EXCLUDED_FEATURES:
            keep_indices.append(i)
    return X[:, keep_indices]

def calculate_bayesian_success(p_esbl, ab_data, alpha=2.0):
    # Bayesian Smoothing
    # P(S|ESBL) = (S_esbl + alpha) / (N_esbl + 2alpha)
    s_esbl = ab_data["ESBL"]["success"]
    n_esbl = ab_data["ESBL"]["total"]
    
    s_non = ab_data["non_ESBL"]["success"]
    n_non = ab_data["non_ESBL"]["total"]
    
    # Eligibility Constraint (Check N)
    if n_esbl < MIN_EVIDENCE_COUNT or n_non < MIN_EVIDENCE_COUNT:
        return 0, 0, "Insufficient Evidence"
        
    prob_s_given_esbl = (s_esbl + alpha) / (n_esbl + 2 * alpha)
    prob_s_given_non = (s_non + alpha) / (n_non + 2 * alpha)
    
    # Total Expected Success
    # P(Success) = P(ESBL) * P(S|ESBL) + (1-P(ESBL)) * P(S|Non)
    expected_success = (p_esbl * prob_s_given_esbl) + ((1 - p_esbl) * prob_s_given_non)
    
    return expected_success, n_esbl + n_non, "OK"

def get_stewardship_weight(drug_code, risk_group):
    # Default weight
    weight = STEWARDSHIP_WEIGHTS.get(drug_code, 0.8) # Default 0.8 for unknown
    
    # Logic: If Risk is HIGH, we relax penalties for Broad Spectrum/Carbapenems
    if risk_group == "High" and drug_code in HIGH_RISK_OVERRIDES:
        weight = 1.0 # Remove penalty, this is appropriate use
        
    # Logic: If Risk is LOW, we increase penalty for Carbapenems
    if risk_group == "Low" and drug_code in ["MEM", "IMP", "ETP"]:
        weight = 0.2 # Strongly discourage
        
    return weight

def assign_confidence(total_n, success_prob, status):
    if status != "OK":
        return "None"
        
    if total_n > 500:
        return "High"
    elif total_n > 100:
        return "Moderate"
    else:
        return "Low"

def generate_recommendation_mock_input():
    # Helper to generate a dummy input matching training features for testing
    # In real integration, this comes from API
    # We will just load X_val from disk and take the first row
    x_val = np.load("Processed/ESBL_Stage2_X_val.npy")
    return x_val[0:1] # Return 2D array (1 row)

def run_recommendation_engine():
    print("🔵 STARTING STAGE 7: RECOMMENDATION ENGINE (TEST RUN)")
    
    # 1. Load
    model, threshold_config, outcomes, feature_names = load_resources()
    t_low = threshold_config["thresholds"]["low"]
    t_high = threshold_config["thresholds"]["high"]
    
    # 2. Mock Input
    X_input_raw = generate_recommendation_mock_input()
    
    # 3. Mask Input
    X_input = apply_masking(X_input_raw, feature_names)
    
    # 4. Predict Risk
    p_esbl = model.predict_proba(X_input)[0, 1]
    
    # 5. Stratify
    risk_group = "Moderate"
    if p_esbl < t_low:
        risk_group = "Low"
    elif p_esbl >= t_high:
        risk_group = "High"
        
    print(f"  Patient Risk Probability: {p_esbl:.4f}")
    print(f"  Risk Group: {risk_group}")
    
    # 6. Rank Antibiotics
    recommendations = []
    
    for drug, data in outcomes.items():
        # Bayesian Success
        exp_success, n_total, status = calculate_bayesian_success(p_esbl, data)
        
        if status != "OK":
            print(f"  Skipping {drug}: {status} (N={n_total})")
            continue
            
        # Stewardship
        weight = get_stewardship_weight(drug, risk_group)
        final_score = exp_success * weight
        
        rec = {
            "Antibiotic": drug,
            "Expected_Success": round(float(exp_success), 4),
            "Stewardship_Weight": round(float(weight), 2),
            "Final_Score": round(float(final_score), 4),
            "Confidence": assign_confidence(n_total, exp_success, status),
            "Note": "Empiric only"
        }
        recommendations.append(rec)
        
    # Sort by Score
    recommendations.sort(key=lambda x: x["Final_Score"], reverse=True)
    
    # Output
    output_json = {
        "esbl_risk": {
            "probability": round(float(p_esbl), 4),
            "group": risk_group
        },
        "recommendations": recommendations[:5], # Top 5
        "warnings": [
            "Empiric guidance only.",
            "De-escalate to narrowest effective agent upon AST confirmation."
        ]
    }
    
    print("\n✅ RECOMMENDATION OUTPUT:")
    print(json.dumps(output_json, indent=4))
    
    # Verification assertions
    assert 0 <= p_esbl <= 1.0
    assert len(recommendations) > 0 or len(outcomes) == 0
    print("\n✅ Verification Passed: No ML training, valid probabilities.")

if __name__ == "__main__":
    run_recommendation_engine()
