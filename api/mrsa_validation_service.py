import logging
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from schemas import ASTPanelEntry

# Config Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MRSAValidationService:
    def __init__(self):
        self.fox_mapping = {"R": True, "S": False, "I": False} # Conservative: I is not MRSA for this study

    def validate(self, db: Session, entry: ASTPanelEntry):
        """
        Validates MRSA predictions against incoming AST data.
        Triggered when organism is Staphylococcus aureus.
        """
        if entry.organism != "Staphylococcus aureus":
            return

        logger.info(f"🔎 Validating MRSA Prediction vs AST for Lab {entry.lab_no}...")
        
        # 1. Determine Ground Truth from Cefoxitin (FOX)
        fox_result = None
        for res in entry.results:
            # Flexible matching for "Cefoxitin" or "Cefoxitin (FOX)"
            if "Cefoxitin" in res.antibiotic:
                fox_result = res.result # 'R', 'S', 'I'
                break
        
        if not fox_result:
            logger.info("   ⚠ No Cefoxitin result found. Skipping validation.")
            return

        actual_mrsa = self.fox_mapping.get(fox_result, False)
        
        # 2. Find Matched Prediction (Logic Option B)
        # Match Prediction: Same Ward, Same Sample Type, Created within last 72h
        # NOTE: This assumes Ward/Sample didn't change and patient flow is consistent.
        
        # Time Window
        time_limit = datetime.now() - timedelta(hours=72)
        
        query = text("""
            SELECT id, risk_band, input_snapshot, 
                   rf_risk_band, lr_risk_band, xgb_risk_band, consensus_band, 
                   consensus_version, confidence_level
            FROM mrsa_risk_assessments
            WHERE ward = :ward
              AND sample_type = :sample
              AND timestamp >= :limit
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        prediction = db.execute(query, {
            "ward": entry.ward,
            "sample": entry.specimen_type,
            "limit": time_limit
        }).fetchone()
        
        if not prediction:
            logger.info("   ℹ No recent prediction found for this Ward/Sample combination.")
            return

        pred_id = prediction[0]
        # Handle cases where detailed bands might be null (pre-Stage C.5 records)
        rf_band = prediction[3] 
        lr_band = prediction[4]
        xgb_band = prediction[5]
        con_band = prediction[6] or prediction[1] # Fallback to main risk_band
        conf_level = prediction[8]
        
        logger.info(f"   ✅ Match Found! Prediction ID: {pred_id} (Consensus: {con_band})")

        # 3. Evaluate Correctness
        # Logic: RED = Predicted MRSA, GREEN/AMBER = Predicted MSSA
        # (Conservative: Amber is technically 'Intermediate Risk', but usually treated as 'Monitor'. 
        #  If actual is MRSA and we said Amber, is it correct? 
        #  Strictly: Fail. But for this audit, let's say RED is the only Positive prediction.)
        
        def is_positive(band):
            return band == "RED"

        rf_correct = (is_positive(rf_band) == actual_mrsa) if rf_band else None
        lr_correct = (is_positive(lr_band) == actual_mrsa) if lr_band else None
        xgb_correct = (is_positive(xgb_band) == actual_mrsa) if xgb_band else None
        con_correct = (is_positive(con_band) == actual_mrsa)

        # 4. Log to Validation Table
        # Construct Model Versions Snapshot (Mock or fetch from DB/Config if possible. 
        # Actually simplest is to just log static snapshot for now as defined in C.5)
        versions_snapshot = {
            "rf": "RF_v1", "lr": "LR_v1", "xgb": "XGB_v1", "consensus": "C5_v1"
        }
        
        log_sql = text("""
            INSERT INTO mrsa_validation_log (
                assessment_id, ward, sample_type,
                cefoxitin_result, actual_mrsa,
                rf_band, lr_band, xgb_band, consensus_band,
                rf_correct, lr_correct, xgb_correct, consensus_correct,
                confidence_level, model_versions
            ) VALUES (
                :id, :ward, :sample,
                :fox, :actual,
                :rf, :lr, :xgb, :con,
                :rf_ok, :lr_ok, :xgb_ok, :con_ok,
                :conf, :vers
            )
        """)
        
        db.execute(log_sql, {
            "id": pred_id,
            "ward": entry.ward,
            "sample": entry.specimen_type,
            "fox": fox_result,
            "actual": actual_mrsa,
            "rf": rf_band, "lr": lr_band, "xgb": xgb_band, "con": con_band,
            "rf_ok": rf_correct, "lr_ok": lr_correct, "xgb_ok": xgb_correct, "con_ok": con_correct,
            "conf": conf_level,
            "vers": json.dumps(versions_snapshot)
        })
        # Commit is handled by caller or here? Main entry endpoint commits. 
        # But if we run in background task, we need our own session or use passed db if sync.
        # Since we use dependency injection in main, we should probably commit here if we passed a session that is kept open?
        # Actually line 212 in main.py adds task `trigger_pipeline_update`.
        # Validation should be synchronous within the transaction OR a background task with new session.
        # The user's code snippet `background_tasks.add_task` implies NEW session.
        
        # For simplicity and transaction safety, let's flush/commit here if DB passed allows it.
        # However, usually we don't commit a passed session unless we own it.
        # Let's assume the caller manages transaction if called synchronously, 
        # or we create a session if called as background task.
        # Given the instruction to modifying `main.py`, I will implement this as a standalone 
        # function that creates its own session if needed, OR accepts one.
        
        # Wait, if this is called from `main.py` inside the `try` block before commit (Line 202-205 in user snippet),
        # then it uses the SAME transaction.
        pass # DB commit will happen in main.py
        
        logger.info(f"   📝 Validation Logged. (Correct: {con_correct})")

mrsa_validation_service = MRSAValidationService()
