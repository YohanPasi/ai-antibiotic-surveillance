import joblib
import pandas as pd
import numpy as np
import os
import logging
from sqlalchemy import create_engine, text
from datetime import datetime

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ARTIFACT_DIR = r'/app/models/mrsa_artifacts'
DATABASE_URL = os.getenv("DATABASE_URL")

# Band Thresholds
GREEN_THRESH = 0.30
AMBER_THRESH = 0.60 # < 0.60 is Amber, >= 0.60 is Red

class MRSAConsensusService:
    def __init__(self):
        self.rf_pipeline = None
        self.lr_pipeline = None
        self.xgb_pipeline = None
        self.engine = None
        self.load_models()
        self.init_db()

    def init_db(self):
        if DATABASE_URL:
            self.engine = create_engine(DATABASE_URL)

    def load_models(self):
        try:
            logger.info("Loading Consensus Models...")
            self.rf_pipeline = joblib.load(os.path.join(ARTIFACT_DIR, 'mrsa_rf_pipeline.pkl'))
            self.lr_pipeline = joblib.load(os.path.join(ARTIFACT_DIR, 'mrsa_lr_pipeline.pkl'))
            self.xgb_pipeline = joblib.load(os.path.join(ARTIFACT_DIR, 'mrsa_xgb_pipeline.pkl'))
            logger.info("✅ All 3 Models Loaded (RF, LR, XGB)")
        except Exception as e:
            logger.error(f"❌ Failed to load models: {e}")
            raise e

    def get_risk_band(self, prob):
        if prob < GREEN_THRESH:
            return "GREEN"
        elif prob < AMBER_THRESH:
            return "AMBER"
        else:
            return "RED"

    def predict_consensus(self, input_df: pd.DataFrame, assessment_id: int = None):
        """
        Runs predictions on all 3 models and determines consensus.
        """
        # 1. Individual Predictions
        # RF
        rf_prob = float(self.rf_pipeline.predict_proba(input_df)[:, 1][0])
        rf_band = self.get_risk_band(rf_prob)
        
        # LR
        lr_prob = float(self.lr_pipeline.predict_proba(input_df)[:, 1][0])
        lr_band = self.get_risk_band(lr_prob)
        
        # XGB
        # Note: XGB might need columns in specific order or types, but Pipeline handles transformation.
        xgb_prob = float(self.xgb_pipeline.predict_proba(input_df)[:, 1][0])
        xgb_band = self.get_risk_band(xgb_prob)

        # 2. Consensus Logic
        bands = [rf_band, lr_band, xgb_band]
        
        # Agreement Counting
        # How many agree with the majority? 
        # Actually simplest is:
        # All 3 same -> High
        # 2 same -> Moderate
        # All 3 diff -> Low
        
        counts = {b: bands.count(b) for b in set(bands)}
        max_agreement = max(counts.values())
        
        final_band = None
        confidence = "LOW"
        
        # Determine Base Final Band & Confidence
        if max_agreement == 3:
            final_band = bands[0] # All same
            confidence = "HIGH"
        elif max_agreement == 2:
            # Find the band with 2 votes
            final_band = [b for b, c in counts.items() if c == 2][0]
            confidence = "MODERATE"
        else:
            # All 3 disagree (e.g. Green, Amber, Red)
            # Default to Median Risk -> AMBER
            final_band = "AMBER"
            confidence = "LOW"
            logger.warning("Models Disagree completely (Green/Amber/Red). Defaulting to AMBER.")

        # 3. Safety Rule: If ANY model says RED, cannot be GREEN
        if "RED" in bands and final_band == "GREEN":
            final_band = "AMBER" # Escalated
            confidence = "MODERATE" # Reduced confidence due to override
            logger.info("Safety Rule Triggered: RED prediction exists, overriding GREEN consensus to AMBER.")

        # 4. Result Object
        result = {
            "consensus_band": final_band,
            "confidence_level": confidence,
            "models": {
                "rf": {"prob": rf_prob, "band": rf_band, "version": "RF_v1"},
                "lr": {"prob": lr_prob, "band": lr_band, "version": "LR_v1"},
                "xgb": {"prob": xgb_prob, "band": xgb_band, "version": "XGB_v1"}
            },
            "consensus_version": "C5_v1"
        }
        
        # 5. Async Database Update (if ID provided)
        if assessment_id and self.engine:
            self.save_consensus_audit(assessment_id, result)
            
        return result

    def save_consensus_audit(self, assessment_id, result):
        try:
            stmt = text("""
                UPDATE mrsa_risk_assessments
                SET 
                    rf_probability = :rf_prob, rf_risk_band = :rf_band, rf_version = :rf_ver,
                    lr_probability = :lr_prob, lr_risk_band = :lr_band, lr_version = :lr_ver,
                    xgb_probability = :xgb_prob, xgb_risk_band = :xgb_band, xgb_version = :xgb_ver,
                    consensus_band = :con_band, confidence_level = :conf, consensus_version = :con_ver
                WHERE id = :id
            """)
            
            with self.engine.connect() as conn:
                conn.execute(stmt, {
                    "rf_prob": result['models']['rf']['prob'],
                    "rf_band": result['models']['rf']['band'],
                    "rf_ver": result['models']['rf']['version'],
                    "lr_prob": result['models']['lr']['prob'],
                    "lr_band": result['models']['lr']['band'],
                    "lr_ver": result['models']['lr']['version'],
                    "xgb_prob": result['models']['xgb']['prob'],
                    "xgb_band": result['models']['xgb']['band'],
                    "xgb_ver": result['models']['xgb']['version'],
                    "con_band": result['consensus_band'],
                    "conf": result['confidence_level'],
                    "con_ver": result['consensus_version'],
                    "id": assessment_id
                })
                conn.commit()
                logger.info(f"Audit record {assessment_id} updated with consensus data.")
        except Exception as e:
            logger.error(f"Failed to save consensus audit: {e}")

# Global Instance
consensus_service = MRSAConsensusService()
