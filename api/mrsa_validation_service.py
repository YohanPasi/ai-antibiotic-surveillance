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

        logger.info(
            f"🔎 Validating MRSA Prediction vs AST — "
            f"Ward={entry.ward} | Specimen={entry.specimen_type} | "
            f"LabNo={entry.lab_no or 'Not provided'} | BHT={entry.bht or 'Not provided'}"
        )
        
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
        
        # ── Time window ────────────────────────────────────────────────────────
        time_limit = datetime.now() - timedelta(hours=72)

        # ══════════════════════════════════════════════════════════════════════
        # 2. TWO-TIER MATCH STRATEGY
        #
        # Tier 1 (Patient-level): Match using BHT or lab_no identifiers.
        #   - BHT is extracted from input_snapshot JSONB (stored at predict time).
        #   - This is the PREFERRED match — no cross-patient confusion possible.
        #
        # Tier 2 (Proximity): Fallback to ward + specimen_type + 72h window.
        #   - Used when no patient identifiers were provided.
        #   - Can produce cross-patient mismatches at high throughput.
        #   - Logs an explicit WARNING so mismatches are traceable.
        # ══════════════════════════════════════════════════════════════════════

        prediction = None
        match_tier = None

        # ── Tier 1: Patient-level (BHT) ───────────────────────────────────────
        if entry.bht:
            tier1_query = text("""
                SELECT id, risk_band, input_snapshot,
                       rf_risk_band, lr_risk_band, xgb_risk_band, consensus_band,
                       consensus_version, confidence_level, model_version
                FROM mrsa_risk_assessments
                WHERE ward = :ward
                  AND sample_type = :sample
                  AND timestamp >= :limit
                  AND input_snapshot->>'bht' = :bht
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            prediction = db.execute(tier1_query, {
                "ward":  entry.ward, "sample": entry.specimen_type,
                "limit": time_limit, "bht":   entry.bht,
            }).fetchone()
            if prediction:
                match_tier = "T1-BHT"
                logger.info(f"   ✅ Tier 1 Match (BHT): Prediction ID {prediction[0]}")

        # ── Tier 1b: Patient-level (lab_no via JSONB snapshot) ─────────────────
        if not prediction and entry.lab_no:
            tier1b_query = text("""
                SELECT id, risk_band, input_snapshot,
                       rf_risk_band, lr_risk_band, xgb_risk_band, consensus_band,
                       consensus_version, confidence_level, model_version
                FROM mrsa_risk_assessments
                WHERE ward = :ward
                  AND sample_type = :sample
                  AND timestamp >= :limit
                  AND input_snapshot->>'lab_no' = :lab_no
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            prediction = db.execute(tier1b_query, {
                "ward":   entry.ward, "sample":  entry.specimen_type,
                "limit":  time_limit, "lab_no": entry.lab_no,
            }).fetchone()
            if prediction:
                match_tier = "T1-LabNo"
                logger.info(f"   ✅ Tier 1b Match (LabNo): Prediction ID {prediction[0]}")

        # ── Tier 2: Proximity fallback ─────────────────────────────────────────
        if not prediction:
            tier2_query = text("""
                SELECT id, risk_band, input_snapshot,
                       rf_risk_band, lr_risk_band, xgb_risk_band, consensus_band,
                       consensus_version, confidence_level, model_version
                FROM mrsa_risk_assessments
                WHERE ward = :ward
                  AND sample_type = :sample
                  AND timestamp >= :limit
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            prediction = db.execute(tier2_query, {
                "ward":  entry.ward, "sample": entry.specimen_type,
                "limit": time_limit,
            }).fetchone()
            if prediction:
                match_tier = "T2-Proximity"
                logger.warning(
                    f"   ⚠ Tier 2 Proximity Match used for Prediction ID {prediction[0]}. "
                    f"No BHT/LabNo provided — cross-patient mismatch possible at high ward throughput."
                )

        if not prediction:
            logger.info("   ℹ No recent prediction found for this Ward/Sample combination.")
            return

        pred_id  = prediction[0]
        rf_band  = prediction[3]
        lr_band  = prediction[4]
        xgb_band = prediction[5]
        con_band = prediction[6] or prediction[1]  # Fallback to main risk_band
        conf_level = prediction[8]

        logger.info(f"   Consensus: {con_band} | Match tier: {match_tier}")

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
        # Derive version from saved model_version field, fallback to v2 defaults
        stored_version = prediction[9] if len(prediction) > 9 else "C5_v2"
        versions_snapshot = {
            "rf": "RF_v2", "lr": "LR_v2", "xgb": "XGB_v2",
            "consensus": stored_version or "C5_v2"
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
        # DB commit is handled by the caller (main.py) — same transaction.
        logger.info(
            f"   📝 Validation Logged — Correct: {con_correct} | "
            f"Fox: {fox_result} | Actual: {'MRSA' if actual_mrsa else 'MSSA'} | "
            f"Predicted: {con_band} | Tier: {match_tier}"
        )

mrsa_validation_service = MRSAValidationService()
