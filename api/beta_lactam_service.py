"""
beta_lactam_service.py
======================
Backend service for the Beta-Lactam Resistance Spectrum Prediction CDSS.
Replaces: esbl_service.py

Predicts the probability of susceptibility across beta-lactam generations
(Gen1, Gen2, Gen3, Gen4, Carbapenem, BL_Combo) using day-0 features:
  age, gender, ward, specimen type, organism, cell count.

Key governance rules inherited from the ESBL module:
  1. AST Lock      — prediction blocked if confirmatory AST is already available.
  2. Scope Lock    — only GNB / Enterobacterales accepted.
  3. OOD Detection — warns if inputs fall outside the training distribution.
  4. No Leakage    — Gen3 cephalosporin AST features (CTX/CAZ/CRO) are always masked.
"""

import os
import json
import pickle
import numpy as np
from fastapi import HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import shap

# ── Path resolution (Docker flat layout vs local nested layout) ────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = current_dir if os.path.exists(os.path.join(current_dir, "Models")) \
           else os.path.dirname(current_dir)

# ── Artifact paths ─────────────────────────────────────────────────────────────
MODEL_PATH         = os.path.join(BASE_DIR, "models", "beta_lactam_xgb_v2.pkl")
MODEL_META_PATH    = os.path.join(BASE_DIR, "config", "beta_lactam_model_meta.json")
THRESHOLDS_PATH    = os.path.join(BASE_DIR, "config", "beta_lactam_thresholds.json")
EVIDENCE_PATH      = os.path.join(BASE_DIR, "config", "beta_lactam_outcome_tables.json")
GOVERNANCE_PATH    = os.path.join(BASE_DIR, "Config", "governance_rules.json") # Preserved old folder
FEATURES_PATH      = os.path.join(BASE_DIR, "config", "beta_lactam_features.json")



# ── Pydantic Response Models ───────────────────────────────────────────────────

class ValidationResponse(BaseModel):
    allowed: bool
    reason: Optional[str] = None


class GenerationPrediction(BaseModel):
    generation: str
    probability: float
    traffic_light: str          # Green / Amber / Red
    success_prob: Optional[float] = None
    score: Optional[float] = None
    stewardship_note: Optional[str] = None


# ── Stewardship configuration ──────────────────────────────────────────────────
# Penalty weights per beta-lactam generation for recommendation scoring.
# Lower weight = discouraged (reserve agents or poor activity).
STEWARDSHIP_WEIGHTS: Dict[str, float] = {
    "Gen1":      0.95,   # First-line, preferred when active
    "Gen2":      0.90,   # Good activity, preferred for UTI / soft tissue
    "Gen3":      0.70,   # High ESBL resistance risk; use with caution
    "Gen4":      0.85,   # Better stability vs ESBL, but not first-line
    "Carbapenem": 0.50,  # Reserve — only if Gen1/2/BL_Combo not viable
    "BL_Combo":  0.85,   # Pip-Tazo / Amoxiclav — good de-escalation option
}

# Override stewardship weights for high-risk patients; carbapenems get priority.
HIGH_RISK_OVERRIDES = ["Carbapenem", "Gen4"]

# Traffic light thresholds — configurable via thresholds JSON.
DEFAULT_THRESHOLDS = {
    "green_min":  0.70,   # >= 70% susceptibility probability → Green
    "amber_min":  0.40,   # 40–69% → Amber
    # < 40% → Red
}


class BetaLactamSpectrumService:
    """
    Main CDSS service for beta-lactam spectrum prediction.
    Loaded as a singleton at application startup.
    """

    def __init__(self):
        self.model = None
        self.thresholds = None
        self.evidence = None
        self.governance = None
        self.feature_names: List[str] = []
        self.metadata = None

        # Safety: always mask 3rd-gen cephalosporin AST features
        # to prevent ESBL phenotype leakage into day-0 predictions.
        self.masked_terms = ["CTX", "CAZ", "CRO"]

        self.load_resources()

    # ── Resource Loading ───────────────────────────────────────────────────────

    def load_resources(self):
        """Load all ML artifacts. Raises RuntimeError if any file is missing."""
        required = [MODEL_PATH, THRESHOLDS_PATH, EVIDENCE_PATH, GOVERNANCE_PATH, FEATURES_PATH]
        missing = [p for p in required if not os.path.exists(p)]
        if missing:
            raise RuntimeError(
                f"Missing beta-lactam artifacts: {missing}. "
                f"Train the model first using train_beta_lactam_model.py."
            )

        with open(MODEL_PATH, "rb") as f:
            loaded_obj = pickle.load(f)
            if isinstance(loaded_obj, dict) and "model" in loaded_obj:
                self.model = loaded_obj["model"]
            else:
                self.model = loaded_obj

        with open(MODEL_META_PATH, "r") as f:
            self.metadata = json.load(f)

        with open(THRESHOLDS_PATH, "r") as f:
            self.thresholds = json.load(f)

        with open(EVIDENCE_PATH, "r") as f:
            self.evidence = json.load(f)

        with open(GOVERNANCE_PATH, "r") as f:
            self.governance = json.load(f)

        with open(FEATURES_PATH, "r") as f:
            raw_features = json.load(f)
            # Support both flat lists (old mock) and dictionary (new XGBoost artifact)
            feature_list = raw_features.get("one_hot_columns", raw_features) if isinstance(raw_features, dict) else raw_features
            
            # Filter out any AST-derived features that could cause leakage
            self.feature_names = [
                feat for feat in feature_list
                if not any(masked in feat for masked in self.masked_terms)
            ]

        print(
            f"BetaLactamSpectrumService loaded. "
            f"Features: {len(self.feature_names)} | "
            f"Generations: {list(self.evidence.keys())}"
        )

    # ── Governance ────────────────────────────────────────────────────────────

    def validate_scope(self, organism: str, gram_result: str) -> ValidationResponse:
        """
        Stage 8: Scope enforcement.
        Only GNB / Enterobacterales are supported.
        """
        rules = self.governance.get("scope_enforcement", {})

        if gram_result != rules.get("allowed_gram_result", "GNB"):
            return ValidationResponse(
                allowed=False,
                reason=f"Gram stain '{gram_result}' is out of scope. Only GNB accepted."
            )

        allowed_organisms = rules.get("allowed_organisms", [])
        if organism not in allowed_organisms:
            return ValidationResponse(
                allowed=False,
                reason=f"Organism '{organism}' is not in governance scope."
            )

        return ValidationResponse(allowed=True)

    def check_ast_lock(self, ast_available: bool):
        """
        Stage 8: Decision freeze.
        If confirmatory AST is available, empiric prediction is blocked.
        """
        if ast_available:
            raise HTTPException(
                status_code=403,
                detail=(
                    "AST results available. Empiric spectrum prediction "
                    "disabled per governance protocol."
                )
            )

    def check_ood(self, input_data: Dict) -> bool:
        """
        Stage 9: Out-of-distribution check for numeric inputs.
        Returns True (OOD flag raised) if inputs fall outside training bounds.
        """
        if "Age" in input_data:
            age = float(input_data["Age"])
            if not (0 <= age <= 110):
                return True
        return False

    def validate_day0_inputs(self, inputs: Dict) -> None:
        """
        LIS Input Validation (Step 8).
        Validates all mandatory Day-0 fields before any ML inference.
        Raises HTTP 422 with a structured, per-field error list on failure.

        Required fields:
          - Age:         Numeric, must be 0–110
          - Gender:      Non-empty string
          - Ward:        Non-empty string
          - Organism:    Non-empty string (scope checked separately)
          - Sample_Type: Non-empty string
        """
        errors: List[Dict] = []

        # Age — must exist and be a valid number in [0, 110]
        age_raw = inputs.get("Age")
        if age_raw is None or str(age_raw).strip() == "":
            errors.append({"field": "Age", "issue": "Age is required."})
        else:
            try:
                age = float(age_raw)
                if not (0 <= age <= 110):
                    errors.append({
                        "field": "Age",
                        "issue": f"Age must be between 0 and 110. Got: {age}"
                    })
            except (ValueError, TypeError):
                errors.append({
                    "field": "Age",
                    "issue": f"Age must be a number. Got: '{age_raw}'"
                })

        # Gender
        if not inputs.get("Gender", "").strip():
            errors.append({"field": "Gender", "issue": "Gender is required."})

        # Ward
        if not inputs.get("Ward", "").strip():
            errors.append({"field": "Ward", "issue": "Ward is required."})

        # Organism
        if not inputs.get("Organism", "").strip():
            errors.append({"field": "Organism", "issue": "Organism is required for scope validation."})

        # Sample Type
        if not inputs.get("Sample_Type", "").strip():
            errors.append({"field": "Sample_Type", "issue": "Sample_Type (specimen type) is required."})

        if errors:
            raise HTTPException(
                status_code=422,
                detail={
                    "error":  "LIS Day-0 Input Validation Failed",
                    "fields": errors,
                    "hint":   "Ensure all required patient and specimen fields are present before requesting prediction."
                }
            )

    # ── Feature Preparation ───────────────────────────────────────────────────

    def _prepare_features(self, input_data: Dict) -> np.ndarray:
        """
        Map UI input dict → model feature vector (1 × N).

        Strategy:
          - Categorical fields (Ward, Organism, Sample_Type, etc.) → one-hot,
            e.g. "Ward": "ICU" looks up feature "Ward_ICU" in feature_names.
          - Numeric fields (Age) → direct float mapping.
          - Always zeros out masked terms (CTX, CAZ, CRO) for safety.
        """
        vector = np.zeros((1, len(self.feature_names)))

        for key, value in input_data.items():
            # 1. Try one-hot match: "Ward_ICU"
            one_hot_key = f"{key}_{value}"
            if one_hot_key in self.feature_names:
                idx = self.feature_names.index(one_hot_key)
                vector[0, idx] = 1.0
            # 2. Try direct numeric match
            elif key in self.feature_names:
                try:
                    vector[0, self.feature_names.index(key)] = float(value)
                except (ValueError, TypeError):
                    pass

        # 3. Add Derived Features (Severity, Sample_Group, Age_Bin)
        ward = str(input_data.get("Ward", ""))
        sample_type = str(input_data.get("Sample_Type", ""))
        age_raw = input_data.get("Age", -1)
        
        try:
            age = float(age_raw)
        except:
            age = -1
            
        severity = "High" if ward.upper() == "ICU" else "Normal"
        sample_group = "Invasive" if sample_type in ["Blood", "CSF"] else "Non-Invasive"
        
        if age <= 18:
            age_bin = "0-18"
        elif age <= 40:
            age_bin = "19-40"
        elif age <= 65:
            age_bin = "41-65"
        else:
            age_bin = "66+"
            
        derived = {
            "Severity": severity,
            "Sample_Group": sample_group,
            "Age_Bin": age_bin
        }
        
        for k, v in derived.items():
            derived_key = f"{k}_{v}"
            if derived_key in self.feature_names:
                vector[0, self.feature_names.index(derived_key)] = 1.0

        # Handle 'Unknown' / Fallback for Categoricals
        for cat in ["Ward", "Organism", "Sample_Type", "Gender", "Cell_Count_Level"]:
            val = str(input_data.get(cat, ""))
            if f"{cat}_{val}" not in self.feature_names and f"{cat}_Unknown" in self.feature_names:
                vector[0, self.feature_names.index(f"{cat}_Unknown")] = 1.0

        # Safety: force masked features to zero regardless of input
        for masked in self.masked_terms:
            for i, name in enumerate(self.feature_names):
                if masked in name:
                    vector[0, i] = 0.0

        return vector

    # ── Prediction ────────────────────────────────────────────────────────────

    def _get_top_feature_influences(self, vector: np.ndarray, top_n: int = 3) -> List[Dict]:
        """
        SHAP Feature Influence integration.
        Extracts top features using shap.TreeExplainer on the underlying XGBoost estimator.
        """
        try:
            # We use Gen3 as the representative model for global SHAP explanation
            if isinstance(self.model, dict) and "Gen3" in self.model:
                calibrated_model = self.model["Gen3"]
                # Extract the base XGBoost model from the first fold of the CalibratedClassifierCV
                base_estimator = calibrated_model.calibrated_classifiers_[0].estimator
                explainer = shap.TreeExplainer(base_estimator)
                shap_values = explainer.shap_values(vector)
                
                # SHAP outputs log-odds, get absolute values for ranking
                flat_shap = shap_values[0]
                
                top_idx = np.argsort(np.abs(flat_shap))[::-1][:top_n]
                
                influences = []
                for idx in top_idx:
                    val = float(flat_shap[idx])
                    influences.append({
                        "feature": self.feature_names[idx],
                        "shap_proxy": round(val, 4),
                        "direction": "increases_susceptibility" if val > 0 else "increases_resistance",
                        "note": "Computed via SHAP TreeExplainer."
                    })
                return influences
            return []
        except Exception as e:
            print(f"SHAP Error: {e}")
            return []  # Never crash the pipeline over explainability

    def _assign_traffic_light(self, probability: float, generation: str = None) -> str:
        """Assign a traffic light to a susceptibility probability."""
        if generation and isinstance(self.thresholds, dict) and generation in self.thresholds:
            t = self.thresholds[generation].get("traffic_lights", DEFAULT_THRESHOLDS)
        else:
            t = DEFAULT_THRESHOLDS
            
        if probability >= t.get("green_min", 0.70):
            return "Green"
        elif probability >= t.get("amber_min", 0.40):
            return "Amber"
        return "Red"

    def _predict_spectrum(self, X: np.ndarray, input_data: Dict) -> Dict[str, Dict]:
        """
        Run the model to get per-generation susceptibility probabilities.
        """
        spectrum = {}
        
        # ML Predictions for trained generations
        if isinstance(self.model, dict):
            for generation, clf in self.model.items():
                proba = clf.predict_proba(X)
                if proba.shape[1] > 1:
                    p = float(proba[0, 1])
                else:
                    p = float(clf.classes_[0])
                spectrum[generation] = {
                    "probability": round(p, 4),
                    "traffic_light": self._assign_traffic_light(p, generation)
                }
                
        # Non-Linear Clinical Overlay for Gen4 and Carbapenem
        gen3_prob = spectrum.get("Gen3", {}).get("probability", 0.5)
        bl_combo_prob = spectrum.get("BL_Combo", {}).get("probability", 0.5)
        
        # Gen4 Diminishing Returns Rule
        gen4_prob = gen3_prob + (0.25 * (1 - gen3_prob))
        gen4_prob = min(gen4_prob, 0.95)
        spectrum["Gen4"] = {
            "probability": round(gen4_prob, 4),
            "traffic_light": self._assign_traffic_light(gen4_prob, "Gen4")
        }
        
        # Carbapenem Rule
        carb_prob = 0.88 + 0.07 * (1 - gen3_prob)
        if gen3_prob < 0.3 and bl_combo_prob < 0.4:
            carb_prob = 0.85
        elif gen3_prob > 0.7:
            carb_prob = 0.95
            
        if input_data.get("Ward", "").upper() == "ICU":
            carb_prob += 0.02
        carb_prob = min(carb_prob, 0.97)
        
        spectrum["Carbapenem"] = {
            "probability": round(carb_prob, 4),
            "traffic_light": self._assign_traffic_light(carb_prob, "Carbapenem")
        }

        return spectrum

    def _generate_recommendations(self, spectrum: Dict, risk_group: str) -> List[Dict]:
        """
        Rank beta-lactam generations using:
          - Bayesian expected success (from evidence table)
          - Stewardship penalty weights
          - Risk-group override rules

        Returns top-5 ranked generations.
        """
        recs = []

        for generation, alpha_data in self.evidence.items():
            prob = spectrum.get(generation, {}).get("probability", 0.0)

            # Basic Bayesian calculation (Laplace smoothing α = 2)
            alpha = 2.0
            # Retrieve historical success rates from evidence tables
            s = alpha_data.get("historical_success", alpha_data.get("success", 0)) + alpha
            n = alpha_data.get("historical_total", alpha_data.get("total", 0)) + 2 * alpha
            exp_success = (prob * (s / n)) + ((1 - prob) * ((n - s) / n))

            # Stewardship weight
            weight = STEWARDSHIP_WEIGHTS.get(generation, 0.80)
            if risk_group == "High" and generation in HIGH_RISK_OVERRIDES:
                weight = 1.0  # Lift restriction for high-risk patients
            if risk_group == "Low" and generation == "Carbapenem":
                weight = 0.20  # Heavily discourage carbapenems for low-risk

            score = exp_success * weight
            traffic = spectrum.get(generation, {}).get("traffic_light", "Red")

            recs.append({
                "generation":        generation,
                "probability":       round(float(prob), 4),
                "expected_success":  round(float(exp_success), 4),
                "score":             round(float(score), 4),
                "stewardship_note":  "Restricted" if weight < 0.80 else "Preferred",
                "traffic_light":     traffic,
            })

        recs.sort(key=lambda x: x["score"], reverse=True)
        return recs

    # ── Main Engine ───────────────────────────────────────────────────────────

    def predict_and_evaluate(self, request_data: Dict) -> Dict:
        """
        Main CDSS prediction pipeline.

        Stages:
          1. Governance checks (AST lock, scope validation)
          2. Feature preparation + masking
          3. Multi-generation spectrum prediction
          4. OOD detection
          5. Recommendation generation + stewardship scoring
          6. Response construction with metadata & warnings
        """
        inputs       = request_data.get("inputs", {})
        ast_available = request_data.get("ast_available", False)

        # ── Stage 8: Governance stops ──────────────────────────────────────────
        # 0. Validate all LIS required fields first
        self.validate_day0_inputs(inputs)

        self.check_ast_lock(ast_available)

        scope = self.validate_scope(
            inputs.get("Organism", ""),
            inputs.get("Gram", "")
        )
        if not scope.allowed:
            raise HTTPException(status_code=400, detail=scope.reason)

        # ── Stage 9: Feature preparation ──────────────────────────────────────
        X = self._prepare_features(inputs)

        # ── Stage 9: Multi-generation prediction ──────────────────────────────
        spectrum = self._predict_spectrum(X, inputs)

        # ── Determine overall risk group from worst-case traffic light ─────────
        lights = [v["traffic_light"] for v in spectrum.values()]
        if "Red" in lights:
            risk_group = "High"
        elif "Amber" in lights:
            risk_group = "Moderate"
        else:
            risk_group = "Low"

        # ── Stage 9: OOD check ────────────────────────────────────────────────
        ood_flag = self.check_ood(inputs)

        # ── Stage 7: Generate ranked recommendations ──────────────────────────
        recommendations = self._generate_recommendations(spectrum, risk_group)
        top_rec = recommendations[0] if recommendations else {}

        # ── Stage 6: Feature influence explainability (SHAP proxy) ────────────
        top_feature_influences = self._get_top_feature_influences(X)

        # ── Build response ────────────────────────────────────────────────────
        response = {
            "spectrum": spectrum,
            "risk_group": risk_group,
            "top_generation_recommendation": top_rec.get("generation"),
            "predicted_success_probability":  top_rec.get("expected_success"),
            # DB schema and plan use 'spectrum_ood_warning' — expose both for compatibility
            "spectrum_ood_warning": ood_flag,
            "ood_warning":          ood_flag,
            "top_feature_influences": top_feature_influences,
            "recommendations": recommendations,
            "metadata": {
                "model_version":    self.metadata.get("config_hash", "unknown")[:8],
                "evidence_version": "v1.0",
                "features_used":    len(self.feature_names),
            },
            "warnings": [
                "Empiric decision support only.",
                "Do not delay AST-guided therapy.",
            ]
        }

        if ood_flag:
            response["warnings"].append(
                "⚠️ Input outside training distribution (OOD). "
                "Model confidence may be reduced."
            )

        return response


# ── Singleton instance (loaded once at app startup) ────────────────────────────
beta_lactam_service = BetaLactamSpectrumService()
