import joblib
import pandas as pd
import numpy as np
import json
import os
import logging
from sqlalchemy import create_engine, text
from datetime import datetime

# ── Setup ──────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ARTIFACT_DIR = r'/app/models/mrsa_artifacts'
DATABASE_URL = os.getenv("DATABASE_URL")

# Risk band thresholds (consistent with Stage 1 design)
GREEN_THRESH = 0.30
AMBER_THRESH = 0.60  # [0.30, 0.60) = AMBER, >= 0.60 = RED

# ── Feature set v2 (must match training) ──────────────────────────────────────
FEATURE_COLS_V2 = [
    'ward',
    'sample_type',
    'gram_stain',
    'cell_count_category',
    'growth_time',
    'recent_antibiotic_use',
    'length_of_stay',
]


class MRSAConsensusService:
    def __init__(self):
        self.rf_pipeline = None
        self.lr_pipeline = None
        self.xgb_pipeline = None
        self.feature_cols = FEATURE_COLS_V2  # fallback constant
        self.engine = None
        self._load_models()
        self._init_db()

    def _init_db(self):
        if DATABASE_URL:
            try:
                self.engine = create_engine(DATABASE_URL)
            except Exception as e:
                logger.error(f"DB init failed: {e}")

    def _load_models(self):
        """Load v2 model artifacts and feature order lock."""
        try:
            logger.info("Loading MRSA Consensus Models (v2)...")
            self.rf_pipeline  = joblib.load(os.path.join(ARTIFACT_DIR, 'mrsa_rf_pipeline_v2.pkl'))
            self.lr_pipeline  = joblib.load(os.path.join(ARTIFACT_DIR, 'mrsa_lr_pipeline_v2.pkl'))
            self.xgb_pipeline = joblib.load(os.path.join(ARTIFACT_DIR, 'mrsa_xgb_pipeline_v2.pkl'))

            # Load feature order lock written by training scripts
            lock_path = os.path.join(ARTIFACT_DIR, 'feature_columns_v2.json')
            if os.path.exists(lock_path):
                with open(lock_path) as f:
                    self.feature_cols = json.load(f)
                logger.info(f"Feature lock loaded: {self.feature_cols}")

            logger.info("✅ All 3 v2 Models Loaded (RF, LR, XGB)")
        except Exception as e:
            logger.error(f"❌ Failed to load v2 models: {e}")
            raise RuntimeError(f"Model load failed: {e}")

    @staticmethod
    def _get_risk_band(prob: float) -> str:
        if prob < GREEN_THRESH:
            return "GREEN"
        elif prob < AMBER_THRESH:
            return "AMBER"
        return "RED"

    def _prepare_input(self, input_dict: dict) -> pd.DataFrame:
        """
        Build the feature DataFrame in the exact column order required by v2 models.
        Applies growth_time NULL → -1 sentinel (non-blood samples).
        """
        df = pd.DataFrame([input_dict])

        # Apply sentinel — NULL growth_time means non-blood sample (clinically informative)
        df['growth_time'] = pd.to_numeric(df.get('growth_time', -1), errors='coerce').fillna(-1)

        # Select only the model feature columns in the locked order
        # (bht and any other record-only fields are silently excluded)
        missing = [c for c in self.feature_cols if c not in df.columns]
        if missing:
            logger.warning(f"Missing feature columns: {missing} — filling with defaults")
            for col in missing:
                df[col] = 'Unknown' if col != 'growth_time' else -1

        return df[self.feature_cols]

    def predict_consensus(self, input_dict: dict) -> dict:
        """
        Run all 3 models on the input and compute consensus.
        Takes a plain dict (not a DataFrame) — single source of truth for feature prep.

        FIX: Previously called twice per prediction (once without ID, once with ID).
        Now called ONCE — returns the result dict. DB write is a separate explicit call.
        """
        X = self._prepare_input(input_dict)

        # Individual model predictions
        rf_prob  = float(self.rf_pipeline.predict_proba(X)[:, 1][0])
        lr_prob  = float(self.lr_pipeline.predict_proba(X)[:, 1][0])
        xgb_prob = float(self.xgb_pipeline.predict_proba(X)[:, 1][0])

        rf_band  = self._get_risk_band(rf_prob)
        lr_band  = self._get_risk_band(lr_prob)
        xgb_band = self._get_risk_band(xgb_prob)

        # Consensus logic — majority vote on bands
        bands = [rf_band, lr_band, xgb_band]
        counts = {b: bands.count(b) for b in set(bands)}
        max_agreement = max(counts.values())

        if max_agreement == 3:
            final_band = bands[0]
            confidence = "HIGH"
        elif max_agreement == 2:
            final_band = [b for b, c in counts.items() if c == 2][0]
            confidence = "MODERATE"
        else:
            # All 3 disagree — default to AMBER (middle ground, safe)
            final_band = "AMBER"
            confidence = "LOW"
            logger.warning("Models disagree completely (GREEN/AMBER/RED). Defaulting to AMBER.")

        # Safety rule: if ANY model says RED, consensus cannot be GREEN
        if "RED" in bands and final_band == "GREEN":
            final_band = "AMBER"
            confidence = "MODERATE"
            logger.info("Safety override: RED exists, escalated GREEN → AMBER.")

        # Consensus probability = weighted average (XGB gets higher weight as champion)
        consensus_prob = round((rf_prob + lr_prob + 2 * xgb_prob) / 4, 4)

        return {
            "consensus_band": final_band,
            "confidence_level": confidence,
            "consensus_probability": consensus_prob,
            "models": {
                "rf":  {"prob": round(rf_prob, 4),  "band": rf_band,  "version": "RF_v2"},
                "lr":  {"prob": round(lr_prob, 4),  "band": lr_band,  "version": "LR_v2"},
                "xgb": {"prob": round(xgb_prob, 4), "band": xgb_band, "version": "XGB_v2"},
            },
            "consensus_version": "C5_v2",
        }

    def save_consensus_audit(self, assessment_id: int, result: dict):
        """Write consensus details back to the audit record (called once, after INSERT)."""
        if not self.engine:
            logger.warning("No DB engine — skipping consensus audit write.")
            return
        try:
            stmt = text("""
                UPDATE mrsa_risk_assessments
                SET
                    rf_probability   = :rf_prob,  rf_risk_band  = :rf_band,  rf_version  = :rf_ver,
                    lr_probability   = :lr_prob,  lr_risk_band  = :lr_band,  lr_version  = :lr_ver,
                    xgb_probability  = :xgb_prob, xgb_risk_band = :xgb_band, xgb_version = :xgb_ver,
                    consensus_band   = :con_band,
                    confidence_level = :conf,
                    consensus_version = :con_ver
                WHERE id = :id
            """)
            with self.engine.connect() as conn:
                conn.execute(stmt, {
                    "rf_prob":  result['models']['rf']['prob'],
                    "rf_band":  result['models']['rf']['band'],
                    "rf_ver":   result['models']['rf']['version'],
                    "lr_prob":  result['models']['lr']['prob'],
                    "lr_band":  result['models']['lr']['band'],
                    "lr_ver":   result['models']['lr']['version'],
                    "xgb_prob": result['models']['xgb']['prob'],
                    "xgb_band": result['models']['xgb']['band'],
                    "xgb_ver":  result['models']['xgb']['version'],
                    "con_band": result['consensus_band'],
                    "conf":     result['confidence_level'],
                    "con_ver":  result['consensus_version'],
                    "id":       assessment_id,
                })
                conn.commit()
                logger.info(f"Consensus audit saved for assessment {assessment_id}.")
        except Exception as e:
            logger.error(f"Failed to save consensus audit: {e}")


# Global singleton — loaded once at API startup
consensus_service = MRSAConsensusService()
