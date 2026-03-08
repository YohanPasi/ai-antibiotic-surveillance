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

ARTIFACT_DIR = r'/app/models/mrsa_artifacts' if os.path.exists('/app') else r'd:\Yohan\Project\api\models\mrsa_artifacts'

# v2 feature columns — used for SHAP explain
FEATURE_COLS_V2 = [
    'ward',
    'sample_type',
    'gram_stain',
    'cell_count_category',
    'growth_time',
    'recent_antibiotic_use',
    'length_of_stay',
]

# Known column names for SHAP display value lookup
KNOWN_FEATURE_COLS = FEATURE_COLS_V2


class MRSAService:
    def __init__(self):
        self.rf_pipeline = None
        self.feature_columns = None
        self.model_version = "RF_v2"
        self._load_artifacts()

    def _load_artifacts(self):
        """Load the RF pipeline (used by SHAP explain) and feature lock."""
        print(f"Loading MRSA Artifacts from {ARTIFACT_DIR}...")
        try:
            self.rf_pipeline = joblib.load(os.path.join(ARTIFACT_DIR, 'mrsa_rf_pipeline_v2.pkl'))

            lock_path = os.path.join(ARTIFACT_DIR, 'feature_columns_v2.json')
            if os.path.exists(lock_path):
                with open(lock_path) as f:
                    self.feature_columns = json.load(f)
            else:
                self.feature_columns = FEATURE_COLS_V2

            # Cache preprocessor and classifier for SHAP
            self.classifier   = self.rf_pipeline.named_steps['classifier']
            self.preprocessor = self.rf_pipeline.named_steps['preprocessor']

            print("MRSA Service Ready (v2).")
        except Exception as e:
            print(f"Failed to load MRSA artifacts: {e}")
            self.rf_pipeline = None

    def predict(self, db: Session, request: MRSAPredictionRequest) -> MRSAPredictionResponse:
        """
        Run consensus prediction and write audit record.

        BUG FIX: The old implementation called consensus_service.predict_consensus() TWICE
        (once to get the result, then again with assessment_id to update the DB).
        Now: predict_consensus() is called ONCE, then save_consensus_audit() is called separately.
        """
        req_dict = request.dict()

        # Strip bht — must never reach the model
        model_input = {k: v for k, v in req_dict.items() if k != 'bht'}

        try:
            from mrsa_consensus_service import consensus_service

            # ── Single consensus call (FIXED double-call bug) ──────────────────
            result = consensus_service.predict_consensus(model_input)

            # ── Primary probability: XGB (champion model) ──────────────────────
            prob  = result['models']['xgb']['prob']
            band  = result['consensus_band']
            confidence = result['confidence_level']

            # ── Stewardship message ────────────────────────────────────────────
            if band == "GREEN":
                msg = "MRSA unlikely based on current specimen data. Standard empiric therapy appropriate."
            elif band == "AMBER":
                msg = "Intermediate risk detected. Review all patient risk factors before prescribing."
            else:
                msg = "High MRSA risk. Consider anti-MRSA coverage pending culture results."

            if confidence != "HIGH":
                msg += f" (Models have {confidence.lower()} agreement — review manually.)"

            # ── Persist audit record (INSERT, THEN update consensus columns) ───
            # Schema version tag on input_snapshot for backward compat of explain()
            snap = {**req_dict, "_schema_version": "v2"}

            insert_sql = text("""
                INSERT INTO mrsa_risk_assessments
                    (ward, sample_type, mrsa_probability, risk_band, model_version, input_snapshot)
                VALUES (:ward, :sample, :prob, :band, :ver, :snap)
                RETURNING id
            """)
            audit_res = db.execute(insert_sql, {
                "ward":   request.ward,
                "sample": request.sample_type,
                "prob":   prob,
                "band":   band,
                "ver":    result['consensus_version'],
                "snap":   json.dumps(snap),
            })
            db.commit()
            assessment_id = audit_res.fetchone()[0]

            # ── Write consensus model breakdown columns (one DB call, not two) ─
            consensus_service.save_consensus_audit(assessment_id, result)

        except Exception as e:
            db.rollback()
            print(f"Prediction failed: {e}")
            raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

        return MRSAPredictionResponse(
            assessment_id=assessment_id,
            mrsa_probability=prob,
            risk_band=band,
            stewardship_message=msg,
            model_version=result['consensus_version'],
            input_snapshot=req_dict,
            consensus_details=result,
        )

    def explain(self, db: Session, assessment_id: int) -> MRSAExplanationResponse:
        """
        Generate SHAP explanations for a stored assessment.
        Supports both v1 (schema_version absent) and v2 snapshots via version detection.
        """
        sql = text("SELECT input_snapshot, risk_band FROM mrsa_risk_assessments WHERE id = :id")
        row = db.execute(sql, {"id": assessment_id}).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Assessment not found.")

        snapshot = row[0]  # dict from JSONB
        risk_band = row[1]

        # ── Schema version detection for backward compatibility ────────────────
        schema_version = snapshot.get("_schema_version", "v1")

        if schema_version == "v1":
            # Remap v1 fields → v2 for SHAP compatibility
            snapshot["gram_stain"] = snapshot.pop("gram_positivity", "Unknown")
            cc = snapshot.pop("cell_count", 0)
            if isinstance(cc, (int, float)):
                snapshot["cell_count_category"] = "LOW" if cc <= 1 else ("MEDIUM" if cc <= 3 else "HIGH")
            else:
                snapshot["cell_count_category"] = "LOW"
            snapshot.setdefault("recent_antibiotic_use", "Unknown")
            snapshot.setdefault("length_of_stay", 0)
            snapshot.pop("age", None)
            snapshot.pop("gender", None)
            snapshot.pop("pus_type", None)

        # ── Build feature DataFrame in v2 locked order ─────────────────────────
        input_df = pd.DataFrame([snapshot])
        input_df['growth_time'] = pd.to_numeric(
            input_df.get('growth_time', pd.Series([-1])), errors='coerce'
        ).fillna(-1)

        # Select only v2 model columns
        for col in FEATURE_COLS_V2:
            if col not in input_df.columns:
                input_df[col] = 'Unknown' if col != 'growth_time' else -1
        input_df = input_df[FEATURE_COLS_V2]

        # ── SHAP computation ───────────────────────────────────────────────────
        try:
            X_transformed = self.preprocessor.transform(input_df)
            explainer = shap.TreeExplainer(self.classifier)
            shap_values = explainer.shap_values(X_transformed, check_additivity=False)

            # Unpack SHAP output (sklearn RF returns list of arrays)
            if isinstance(shap_values, list):
                vals = shap_values[1][0] if len(shap_values) >= 2 else shap_values[0][0]
            elif len(shap_values.shape) == 3:
                vals = shap_values[0, :, 1]
            else:
                vals = shap_values[0]

        except Exception as e:
            print(f"SHAP error: {e}")
            raise HTTPException(status_code=500, detail=f"Explanation failed: {str(e)}")

        # ── Map SHAP values → feature names ───────────────────────────────────
        try:
            ohe_cats = self.preprocessor.named_transformers_['cat'].get_feature_names_out(
                input_features=FEATURE_COLS_V2[:5]  # categorical features only
            )
            num_feats = ['growth_time', 'length_of_stay']
            all_feats = list(ohe_cats) + num_feats  # must match ColumnTransformer order (cat first)

            print(f"DEBUG: all_feats={len(all_feats)}, vals={len(vals)}")

            explanations = []
            for feat_name, impact in zip(all_feats, vals):
                impact = float(np.ravel(impact)[0]) if isinstance(impact, (list, np.ndarray)) else float(impact)

                # Minimum impact filter — suppress noise
                if abs(impact) < 0.015:
                    continue

                # Inactive OHE category filter — only show the active category
                for col in FEATURE_COLS_V2:
                    prefix = f"{col}_"
                    if feat_name.startswith(prefix):
                        feat_val_suffix = feat_name[len(prefix):]
                        actual_val = str(input_df.iloc[0].get(col, ""))
                        if actual_val.lower().strip() != feat_val_suffix.lower().strip():
                            break  # skip inactive OHE category
                else:
                    pass  # numeric features — always show

                # Clean display name
                clean_name = feat_name.replace("_", " ").title()

                # Display value — find matching original column
                display_val = ""
                for col in FEATURE_COLS_V2:
                    if col in feat_name.lower():
                        display_val = str(input_df.iloc[0].get(col, ""))
                        break

                explanations.append({
                    "feature": clean_name,
                    "impact": round(impact, 4),
                    "value": display_val,
                })

            explanations.sort(key=lambda x: abs(x["impact"]), reverse=True)

            return MRSAExplanationResponse(
                assessment_id=assessment_id,
                risk_band=risk_band,
                explanations=explanations[:10],
            )

        except Exception as e:
            print(f"Feature mapping failed: {e}")
            raise HTTPException(status_code=500, detail="Could not map explanations.")


mrsa_service = MRSAService()
