import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import pandas as pd
from mrsa_schemas import (
    AnalyticsSummaryResponse, SafetyMetrics, StewardshipMetrics, 
    MetricValue, WardRiskMetric, GovernanceDecisionCreate
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MRSAAnalyticsService:
    def __init__(self):
        # Hardcoded Baseline (Stage E Requirement: Fixed Baseline)
        self.BASELINE = {
            "npv": 95.0,
            "sensitivity": 90.0,
            "fn_limit": 0
        }
        self.VANCO_COURSE_DAYS = 7.0 # Assumed days saved per avoided empirical course

    def get_summary(self, db: Session) -> AnalyticsSummaryResponse:
        """
        Computes 30-day Rolling Performance Metrics.
        """
        # 1. Fetch Window Data (Last 30 Days)
        window_start = datetime.now() - timedelta(days=30)
        
        query = text("""
            SELECT
                actual_mrsa,
                consensus_band,
                rf_band,
                lr_band,
                xgb_band
            FROM mrsa_validation_log
            WHERE validation_date >= :start
        """)
        rows = db.execute(query, {"start": window_start}).fetchall()
        
        total = len(rows)
        if total == 0:
            return self._empty_response()

        # 2. Compute Metrics
        # Logic: Red = Positive, Green/Amber = Negative (Screening Context)
        # False Negative: Actual=TRUE (True MRSA), Pred != RED
        
        fn_count = 0
        tp_count = 0
        tn_count = 0
        fp_count = 0
        
        # Multi-model tracking
        rf_correct = 0
        xgb_correct = 0

        lr_correct = 0  # was missing from old implementation

        for row in rows:
            actual  = row[0]   # Boolean
            con_band = row[1]
            rf_band  = row[2]
            lr_band  = row[3]  # FIX: was previously using xgb_band column for LR
            xgb_band = row[4]

            is_pred_positive = (con_band == "RED")

            if actual and not is_pred_positive:
                fn_count += 1
            elif actual and is_pred_positive:
                tp_count += 1
            elif not actual and not is_pred_positive:
                tn_count += 1
            elif not actual and is_pred_positive:
                fp_count += 1

            # Per-model accuracy (RED vs non-RED)
            if (rf_band  == "RED") == actual: rf_correct  += 1
            if (lr_band  == "RED") == actual: lr_correct  += 1  # FIX: now using correct column
            if (xgb_band == "RED") == actual: xgb_correct += 1

        # Calculate Rates
        # NPV = TN / (TN + FN)
        npv = (tn_count / (tn_count + fn_count) * 100) if (tn_count + fn_count) > 0 else 0.0
        
        # Sensitivity = TP / (TP + FN)
        sensitivity = (tp_count / (tp_count + fn_count) * 100) if (tp_count + fn_count) > 0 else 0.0
        
        # Stewardship Impact
        # Green/Amber Correct (TN) = Potentially avoided Vanco
        vanco_days = tn_count * self.VANCO_COURSE_DAYS 
        # Early Detection (TP) = Benefit
        
        # 3. Status Determination vs Baseline
        npv_status = "OK"
        if npv < self.BASELINE['npv']: npv_status = "CRITICAL"
        
        sens_status = "OK"
        if sensitivity < self.BASELINE['sensitivity']: sens_status = "WARNING"
        
        if fn_count > 0: 
            # Depending on policy, even 1 FN might be warning, but let's stick to NPV driving critical
            pass

        return AnalyticsSummaryResponse(
            safety=SafetyMetrics(
                formatted_npv=MetricValue(
                    value=round(npv, 1), 
                    status=npv_status, 
                    trend="STABLE" # Todo: Real trend needs comparison with prev window
                ),
                formatted_sensitivity=MetricValue(
                    value=round(sensitivity, 1),
                    status=sens_status,
                    trend="STABLE"
                ),
                false_negatives_count=fn_count,
                total_validations=total
            ),
            stewardship=StewardshipMetrics(
                vanco_days_saved=vanco_days,
                early_detection_count=tp_count
            ),
            model_health={
                "rf_acc":        round(rf_correct  / total, 2),
                "lr_acc":        round(lr_correct  / total, 2),  # FIX: now tracked correctly
                "xgb_acc":       round(xgb_correct / total, 2),
                "consensus_acc": round((tp_count + tn_count) / total, 2)
            },
            governance_status=self.governance_check({"sensitivity": sensitivity, "npv": npv, "fn": fn_count})
        )

    def _empty_response(self):
        return AnalyticsSummaryResponse(
            safety=SafetyMetrics(
                formatted_npv=MetricValue(value=0, status="OK", trend="STABLE"),
                formatted_sensitivity=MetricValue(value=0, status="OK", trend="STABLE"),
                false_negatives_count=0,
                total_validations=0
            ),
            stewardship=StewardshipMetrics(vanco_days_saved=0, early_detection_count=0),
            model_health={},
            governance_status="NO_DATA"
        )

    def get_ward_risk_heatmap(self, db: Session):
        # Rolling 14 Days Heatmap (Active MRSA Pressure)
        # Based on Predictions (mrsa_risk_assessments), NOT Validation
        # This shows "Risk Density"
        
        start_date = datetime.now() - timedelta(days=14)
        query = text("""
            SELECT ward, risk_band, COUNT(*) as cnt
            FROM mrsa_risk_assessments
            WHERE timestamp >= :start AND ward IS NOT NULL AND ward != ''
            GROUP BY ward, risk_band
        """)
        rows = db.execute(query, {"start": start_date}).fetchall()
        
        # Aggregation in Python
        wards = {}
        for r in rows:
            w = r[0]
            band = r[1]
            c = r[2]
            
            if w not in wards: wards[w] = {"total": 0, "red": 0}
            wards[w]["total"] += c
            if band == "RED":
                wards[w]["red"] += c
                
        results = []
        for w, data in wards.items():
            red_rate = (data["red"] / data["total"]) * 100
            
            alert = "LOW"
            if red_rate > 30: alert = "HIGH"
            elif red_rate > 10: alert = "MODERATE"
            
            results.append(WardRiskMetric(
                ward=w,
                red_rate=round(red_rate, 1),
                total_predictions=data["total"],
                trend="STABLE", # Placeholder
                alert_level=alert
            ))
            
        return sorted(results, key=lambda x: x.red_rate, reverse=True)

    @staticmethod
    def governance_check(metrics: dict) -> str:
        """
        Determine governance action based on live safety metrics.
        Called automatically from get_summary() and the /api/mrsa/governance/status endpoint.

        Thresholds (clinical research defaults):
          DISABLE_MODULE  — NPV < 70% (too many missed MRSA cases)
          RETRAIN_REVIEW  — Sensitivity < 80% OR NPV < 85%
          MONITOR         — Sensitivity < 90% (within acceptable range but close to limit)
          ACTIVE          — All metrics within safe thresholds
        """
        npv         = metrics.get("npv", 100)
        sensitivity = metrics.get("sensitivity", 100)
        fn          = metrics.get("fn", 0)

        if npv < 70:
            return "DISABLE_MODULE"    # Unsafe — too many missed MRSA cases
        if sensitivity < 80 or npv < 85:
            return "RETRAIN_REVIEW"    # Performance degraded — trigger retraining workflow
        if sensitivity < 90:
            return "MONITOR"           # Borderline — watch closely
        return "ACTIVE"                # All clear

    def get_governance_status(self, db: Session) -> dict:
        """
        Standalone governance status endpoint — returns current model health decision
        along with the metrics that drove it, without the full analytics payload.
        """
        window_start = datetime.now() - timedelta(days=30)
        query = text("""
            SELECT actual_mrsa, consensus_band
            FROM mrsa_validation_log
            WHERE validation_date >= :start
        """)
        rows = db.execute(query, {"start": window_start}).fetchall()

        if not rows:
            return {
                "governance_status": "NO_DATA",
                "message": "No validation data in the last 30 days. Run AST entry for Staphylococcus aureus to populate.",
                "metrics": {}
            }

        total = len(rows)
        tp = sum(1 for r in rows if r[0] and r[1] == "RED")
        tn = sum(1 for r in rows if not r[0] and r[1] != "RED")
        fn = sum(1 for r in rows if r[0] and r[1] != "RED")

        sensitivity = round((tp / (tp + fn) * 100) if (tp + fn) > 0 else 0, 1)
        npv         = round((tn / (tn + fn) * 100) if (tn + fn) > 0 else 0, 1)

        status = self.governance_check({"sensitivity": sensitivity, "npv": npv, "fn": fn})

        # Human-readable recommendation
        recommendations = {
            "ACTIVE":         "System operating within safe clinical thresholds. Continue monitoring.",
            "MONITOR":        "Sensitivity approaching lower limit. Increase validation frequency.",
            "RETRAIN_REVIEW": "Performance below threshold. Schedule model retraining before next release.",
            "DISABLE_MODULE": "CRITICAL: NPV below safe limit. Disable MRSA module until retrained and validated.",
        }

        return {
            "governance_status": status,
            "message": recommendations[status],
            "metrics": {
                "sensitivity_pct": sensitivity,
                "npv_pct": npv,
                "false_negatives": fn,
                "true_positives": tp,
                "total_validations": total,
                "window_days": 30
            }
        }

    def log_decision(self, db: Session, decision: GovernanceDecisionCreate, admin_user: str):
        query = text("""
            INSERT INTO mrsa_governance_decisions 
            (triggered_by, decision, decided_by, notes)
            VALUES (:reason, :dec, :user, :notes)
        """)
        db.execute(query, {
            "reason": decision.triggered_by,
            "dec": decision.decision,
            "user": admin_user,
            "notes": decision.notes
        })
        db.commit()
        logger.info(f"⚖ Governance Decision Logged: {decision.decision} by {admin_user}")

mrsa_analytics_service = MRSAAnalyticsService()
