
import numpy as np
import json
import os
import sys
import pickle
import datetime
import pandas as pd
from xgboost import XGBClassifier
from sklearn.metrics import confusion_matrix
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Constants
X_VAL_PATH = "Processed/ESBL_Stage2_X_val.npy"
Y_VAL_PATH = "Processed/ESBL_Stage2_y_val.npy"
FEATURES_PATH = "Processed/ESBL_Stage2_feature_names.json"
MODEL_PATH = "Models/esbl_xgb_early_v1.pkl"
OUTPUT_CONFIG_PATH = "Config/esbl_early_thresholds.json"
EXCLUDED_FEATURES = ["CTX", "CAZ", "CRO"]
MIN_GROUP_SIZE_PCT = 0.05 # Minimum 5% of cohort size for a risk group

def load_data():
    print("Loading Validation Data and Model...")
    if not os.path.exists(MODEL_PATH):
        print(f"❌ Model file missing: {MODEL_PATH}")
        sys.exit(1)
        
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
        
    X_val = np.load(X_VAL_PATH)
    y_val = np.load(Y_VAL_PATH)
    
    with open(FEATURES_PATH, 'r') as f:
        feature_names = json.load(f)
        
    return model, X_val, y_val, feature_names

def apply_masking(X_val, feature_names):
    print("Applying Feature Masking (Strict Consistency)...")
    keep_indices = []
    
    for i, name in enumerate(feature_names):
        if name in EXCLUDED_FEATURES:
            print(f"  Filtering out: {name}")
        else:
            keep_indices.append(i)
            
    X_val_masked = X_val[:, keep_indices]
    
    # Assert feature count (37 -> 34 expected)
    if X_val_masked.shape[1] != 34 and len(feature_names) == 37:
         print(f"⚠️ Warning: Expected 34 features, got {X_val_masked.shape[1]}. Check exclusions.")
    
    return X_val_masked

def calculate_metrics(y_true, y_prob, threshold):
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    total = tn + fp + fn + tp
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
    fn_rate = fn / (fn + tp) if (fn + tp) > 0 else 0 # Miss rate among positives
    
    return {
        "threshold": float(threshold),
        "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
        "npv": float(npv),
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "ppv": float(ppv),
        "fn_rate": float(fn_rate),
        "pos_rate": float((tp+fp)/total)
    }

def select_thresholds(sweep_results, y_prob):
    print("Selecting Thresholds...")
    
    # Convert to DataFrame for easier querying
    df = pd.DataFrame(sweep_results)
    
    # T_low (Rule-out): Maximize NPV, minimize FN Rate
    # Strategy: Find thresholds with NPV >= 0.90 (if poss), then pick one with lowest FN rate
    # If not possible, pick max NPV. 
    # Constraint: 'pos_rate' (predicted positive) shouldn't be 100% or 0%
    # Constraint: Group size > MIN_GROUP_SIZE_PCT
    
    # Let's target high NPV first.
    candidates_low = df[df['npv'] >= 0.90]
    
    if candidates_low.empty:
        print("  ⚠️ No threshold found with NPV >= 0.90. Maximizing NPV.")
        best_low = df.loc[df['npv'].idxmax()]
    else:
        # Among high NPV, ensure we actually rule out some people (pos_rate < 1.0)
        # And ensure low risk group size (1 - pos_rate) is significant
        candidates_low = candidates_low[candidates_low['pos_rate'] <= (1.0 - MIN_GROUP_SIZE_PCT)]
        if candidates_low.empty:
             best_low = df.loc[df['npv'].idxmax()]
        else:
             # Pick max NPV
             best_low = candidates_low.loc[candidates_low['npv'].idxmax()]
             
    t_low = best_low['threshold']
    
    # T_high (Rule-in): Balancing Sensitivity/Specificity, or High PPV
    # We want a high probability group.
    # Look for PPV > 0.5 or high Specificity
    # Must be > T_low
    
    candidates_high = df[df['threshold'] > t_low]
    
    # Heuristic: Maximize Youden's J (Sens + Spec - 1) for general performance, 
    # OR prioritize PPV for definite "High Risk"
    # Given the low AUROC, high PPV might be hard. Let's maximize Specificity to be sure about High Risk
    # within reasonable Sensitivity.
    
    if candidates_high.empty:
        # Fallback if t_low is very high
        t_high = min(t_low + 0.2, 0.95)
    else:
        # Ensure High Risk group size > MIN_GROUP_SIZE_PCT (pos_rate > 0.05)
        candidates_high = candidates_high[candidates_high['pos_rate'] >= MIN_GROUP_SIZE_PCT]
        if candidates_high.empty:
             candidates_high = df[df['threshold'] > t_low] # Revert constraint
             
        if not candidates_high.empty:
             # Maximize Specificity (Confidence in Rule-In)
             best_high = candidates_high.loc[candidates_high['specificity'].idxmax()]
             t_high = best_high['threshold']
        else:
             t_high = 0.8 # Default fall back
             
    print(f"  Selected T_low: {t_low} (NPV: {best_low['npv']:.4f})")
    print(f"  Selected T_high: {t_high}")
    
    return t_low, t_high

def evaluate_strata(y_val, y_prob, t_low, t_high):
    print("Evaluating Risk Strata...")
    
    total = len(y_val)
    
    # Low Risk
    low_mask = y_prob < t_low
    low_count = np.sum(low_mask)
    low_prev = np.mean(y_val[low_mask]) if low_count > 0 else 0
    # NPV is TN / (TN+FN) in this group? No, NPV is global ability to say 'Negative' if < T.
    # Actually, for the stratum, we want to know Actual Negative rate (1-Prevalence).
    # Global NPV corresponds to "If I call everyone < T_low Negative, how often am I right?"
    
    # Moderate Risk
    mod_mask = (y_prob >= t_low) & (y_prob < t_high)
    mod_count = np.sum(mod_mask)
    mod_prev = np.mean(y_val[mod_mask]) if mod_count > 0 else 0
    
    # High Risk
    high_mask = y_prob >= t_high
    high_count = np.sum(high_mask)
    high_prev = np.mean(y_val[high_mask]) if high_count > 0 else 0
    
    strata_metrics = {
        "low_risk": {
            "range": f"< {t_low}",
            "count": int(low_count),
            "pct_cohort": float(low_count/total),
            "esbl_prevalence": float(low_prev),
            "npv_of_stratum": float(1 - low_prev) # Probability of NOT having ESBL in this group
        },
        "moderate_risk": {
            "range": f"{t_low} - {t_high}",
            "count": int(mod_count),
            "pct_cohort": float(mod_count/total),
            "esbl_prevalence": float(mod_prev)
        },
        "high_risk": {
            "range": f">= {t_high}",
            "count": int(high_count),
            "pct_cohort": float(high_count/total),
            "esbl_prevalence": float(high_prev),
            "ppv_of_stratum": float(high_prev) # Probability of HAVING ESBL in this group
        }
    }
    
    return strata_metrics

def stage6_thresholds():
    print("🔵 STARTING STAGE 6: THRESHOLD OPTIMIZATION")
    
    # 1. Load
    model, X_val, y_val, feature_names = load_data()
    print("  Note: Optimization strictly on Validation Set.")
    
    # 2. Mask
    X_val_masked = apply_masking(X_val, feature_names)
    
    # 3. Probabilities
    y_prob = model.predict_proba(X_val_masked)[:, 1]
    print(f"  Probabilities: Min={y_prob.min():.4f}, Max={y_prob.max():.4f}, Mean={y_prob.mean():.4f}")
    
    # 4. Sweep
    print("Running Threshold Sweep...")
    sweep_results = []
    for t in np.arange(0.05, 0.96, 0.05):
        m = calculate_metrics(y_val, y_prob, t)
        sweep_results.append(m)
        
    # 5. Selection
    t_low, t_high = select_thresholds(sweep_results, y_prob)
    
    # 6. Evaluation
    strata_metrics = evaluate_strata(y_val, y_prob, t_low, t_high)
    
    # 7. Validation of Safety Constraints
    # Check if Low Risk Group is too small
    if strata_metrics["low_risk"]["pct_cohort"] < MIN_GROUP_SIZE_PCT:
        print("⚠️ WARNING: Low Risk group is < 5% of cohort. Thresholds might be unstable.")
        
    # 8. Save
    print("Saving Config...")
    
    output_data = {
        "thresholds": {
            "low": float(t_low),
            "high": float(t_high)
        },
        "selection_rationale": {
            "low": "Maximized NPV under constraint of rule-out rate > 0",
            "high": "Selected for higher Specificity/PPV to identify likely positives",
            "note": "Thresholds are fixed post-hoc decision parameters and are not learned by the model."
        },
        "risk_group_definitions": {
            "Low": f"Probability < {t_low}",
            "Moderate": f"{t_low} <= Probability < {t_high}",
            "High": f"Probability >= {t_high}"
        },
        "clinical_statement": "This risk stratification supports empiric decision-making only and does not replace AST-based confirmation.",
        "performance_by_stratum": strata_metrics,
        "validation_sweep_summary": sweep_results
    }
    
    with open(OUTPUT_CONFIG_PATH, 'w') as f:
        json.dump(output_data, f, indent=4)
        
    print("-" * 30)
    print("✅ STAGE 6 COMPLETED SUCCESSFULLY")
    print(f"Config saved: {OUTPUT_CONFIG_PATH}")
    print("Low Risk NPV:", strata_metrics["low_risk"]["npv_of_stratum"])
    print("-" * 30)

if __name__ == "__main__":
    stage6_thresholds()
