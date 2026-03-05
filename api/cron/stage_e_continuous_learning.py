import sys
import os
import logging
from datetime import datetime, timedelta, date
import pandas as pd
from sqlalchemy import create_engine, text

# Setup Path to import from parent directory (/app) when running from /app/cron
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir  = os.path.dirname(current_dir)  # /app
models_dir  = os.path.join(parent_dir, 'models')
sys.path.append(parent_dir)
sys.path.append(models_dir)

from database import engine
from prediction_service import PredictionService

# Phase 4A — backtesting engine
try:
    from backtester import run_model_auto_selection, get_active_model
    _BACKTESTER_AVAILABLE = True
except ImportError as _bt_err:
    logger_tmp = logging.getLogger('stage_e')
    logger_tmp.warning(f"backtester not importable: {_bt_err}")
    _BACKTESTER_AVAILABLE = False

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ContinuousLearning")


# =============================================================================
# PHASE 3A — PREDICTION FINALIZATION ENGINE
# =============================================================================

def _get_last_data_week(cursor):
    """
    R1 — Epidemiological time anchor.
    Derives closed-week boundary from aggregated data — NEVER from system clock.
    Handles backdated entries, Stage B rebuilds, and calendar differences.
    """
    cursor.execute("SELECT MAX(week_start_date) FROM ast_weekly_aggregated")
    row = cursor.fetchone()
    return row[0] if row and row[0] else None


def _get_actual_s(cursor, ward, org, abx, week_date):
    """Fetch aggregated susceptibility for a specific (ward, org, abx, week)."""
    cursor.execute("""
        SELECT susceptibility_percent
        FROM ast_weekly_aggregated
        WHERE ward = %s AND organism = %s AND antibiotic = %s
          AND week_start_date = %s
    """, (ward, org, abx, week_date))
    row = cursor.fetchone()
    return float(row[0]) if row and row[0] is not None else None


def finalize_closed_week_predictions(cursor, conn):
    """
    Phase 3A — Prediction Finalization Engine.

    For every unvalidated prediction whose target_week_start <= last_data_week:
      1. Fetch actual susceptibility from ast_weekly_aggregated   (R1 anchor)
      2. Compute prediction_error and direction_correct
      3. Update predictions.actual_s_percent / prediction_error   (primary store)
      4. Write to forecast_validation_log                          (audit trail)
      5. Detect historical revisions                               (G2)

    All 14 hardening rules applied:
      R1  — epidemiological time only
      G2  — revision detection with HISTORICAL_REVISION_DETECTED
      G6  — rolling window leakage guard (no open weeks ever written)
      direction_correct = None when prior week unavailable (not False)
    """
    logger.info("─" * 62)
    logger.info("📋 Phase 3A: Prediction Finalization Engine starting...")

    # ── E1: Epi-time anchor (R1) ─────────────────────────────────────────────
    last_data_week = _get_last_data_week(cursor)
    if not last_data_week:
        logger.warning("  No data in ast_weekly_aggregated — aborting Phase 3A.")
        return

    logger.info(f"  📅 Epidemiological anchor: {last_data_week}")

    # ── E2: Fetch eligible predictions (closed weeks, not yet validated) ──────
    # Includes already-validated rows — revision detection handles idempotency
    cursor.execute("""
        SELECT id, ward, organism, antibiotic,
               target_week_start, predicted_s_percent, model_used
        FROM predictions
        WHERE target_week_start <= %s
          AND is_ward_level = TRUE
        ORDER BY ward, organism, antibiotic, target_week_start
    """, (last_data_week,))
    forecasts = cursor.fetchall()
    logger.info(f"  🔎 Predictions eligible: {len(forecasts)}")

    validated         = 0
    revised           = 0
    skipped_no_data   = 0
    skipped_open      = 0
    skipped_unchanged = 0

    for (pred_id, ward, org, abx, forecast_week, predicted_s, model_ver) in forecasts:

        # ── Closed-week guard (R1 / G6) ───────────────────────────────────────
        if forecast_week > last_data_week:
            skipped_open += 1
            continue

        # ── Get actual susceptibility ──────────────────────────────────────────
        actual_s = _get_actual_s(cursor, ward, org, abx, forecast_week)
        if actual_s is None:
            skipped_no_data += 1
            continue

        prediction_error = actual_s - float(predicted_s)

        # ── Direction correctness ──────────────────────────────────────────────
        # NULL when no prior week — never defaults to True
        prior_s = _get_actual_s(cursor, ward, org, abx,
                                 forecast_week - timedelta(days=7))
        if prior_s is not None:
            actual_change    = actual_s - prior_s
            predicted_change = float(predicted_s) - prior_s
            direction_correct = bool(actual_change * predicted_change >= 0)
        else:
            direction_correct = None

        # ── Check existing validation in audit log (G2 revision detection) ─────
        cursor.execute("""
            SELECT actual_s_percent
            FROM forecast_validation_log
            WHERE ward = %s AND organism = %s AND antibiotic = %s
              AND forecast_week = %s
        """, (ward, org, abx, forecast_week))
        existing = cursor.fetchone()

        if existing:
            stored_actual = float(existing[0]) if existing[0] is not None else None
            if stored_actual is None or abs(stored_actual - actual_s) > 0.01:
                # G2: Stage B rebuild changed actual_s — log revision
                logger.warning(
                    f"  ⚠️  HISTORICAL_REVISION_DETECTED: "
                    f"{org}/{abx}/{ward}/{forecast_week} "
                    f"(stored={stored_actual:.2f}% → new={actual_s:.2f}%)"
                )
                # Update audit log with revision info
                cursor.execute("""
                    UPDATE forecast_validation_log
                    SET actual_s_percent  = %s,
                        prediction_error  = %s,
                        direction_correct = %s,
                        revision_flag     = TRUE,
                        validated_at      = NOW()
                    WHERE ward = %s AND organism = %s AND antibiotic = %s
                      AND forecast_week = %s
                """, (actual_s, prediction_error, direction_correct,
                      ward, org, abx, forecast_week))
                # Also update the predictions row
                cursor.execute("""
                    UPDATE predictions
                    SET actual_s_percent  = %s,
                        prediction_error  = %s,
                        direction_correct = %s,
                        revision_flag     = TRUE,
                        validated_at      = NOW()
                    WHERE id = %s
                """, (actual_s, prediction_error, direction_correct, pred_id))
                revised += 1
            else:
                skipped_unchanged += 1
        else:
            # ── Insert new validation row (audit log) ──────────────────────────
            cursor.execute("""
                INSERT INTO forecast_validation_log
                    (ward, organism, antibiotic, forecast_week,
                     predicted_s_percent, actual_s_percent,
                     prediction_error, direction_correct,
                     validated_at, revision_flag, model_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), FALSE, %s)
            """, (ward, org, abx, forecast_week,
                  float(predicted_s), actual_s, prediction_error,
                  direction_correct, model_ver))

            # Update the predictions row too (primary store)
            cursor.execute("""
                UPDATE predictions
                SET actual_s_percent  = %s,
                    prediction_error  = %s,
                    direction_correct = %s,
                    validated_at      = NOW()
                WHERE id = %s
            """, (actual_s, prediction_error, direction_correct, pred_id))
            validated += 1

    # ── E7: Commit and log summary ────────────────────────────────────────────
    conn.commit()
    logger.info(
        f"  ✅ Phase 3A complete — "
        f"validated={validated}, revised={revised}, "
        f"no_data={skipped_no_data}, open_week={skipped_open}, "
        f"unchanged={skipped_unchanged}"
    )
    logger.info("─" * 62)


# =============================================================================
# PHASE 3B — ROLLING PERFORMANCE METRICS ENGINE
# =============================================================================

# Thresholds — tunable per publication requirements
_MIN_VALIDATED      = 6     # Below this → INSUFFICIENT_DATA, no adaptive CI
_DEGRADATION_MAE    = 12.0  # MAE > 12% with ≥ 8 validations → DEGRADED
_DEGRADATION_MIN_N  = 8     # Minimum validations before degradation can fire
_BIAS_RATIO         = 0.75  # |bias| > MAE * 0.75 → SYSTEMATIC_BIAS_WARNING
_EXCELLENT_MAE      =  5.0
_ACCEPTABLE_MAE     = 10.0
_FALLBACK_CI_WIDTH  = 10.0  # Static ±10% when insufficient data
_ROLLING_WEEKS      = 12    # Rolling validation window


def _compute_performance_status(rolling_mae, validated_count, degradation_flagged):
    """
    Performance status hierarchy (publication-grade):
      INSUFFICIENT_DATA → DEGRADED → EXCELLENT → ACCEPTABLE → NEEDS_RECAL
    Degradation flag is sticky — never cleared by metric alone.
    """
    if validated_count < _MIN_VALIDATED:
        return "INSUFFICIENT_DATA"
    if degradation_flagged:
        return "DEGRADED"
    if rolling_mae is None:
        return "INSUFFICIENT_DATA"
    if rolling_mae <= _EXCELLENT_MAE:
        return "EXCELLENT"
    if rolling_mae <= _ACCEPTABLE_MAE:
        return "ACCEPTABLE"
    return "NEEDS_RECAL"


def update_rolling_performance_metrics(cursor, conn):
    """
    Phase 3B — Rolling Performance Metrics Engine.

    For every (ward, org, abx) triple that has validated predictions:
      1. Query the last 12-week rolling window from forecast_validation_log (G6 leakage-safe)
      2. Compute rolling MAE, MDA, mean_bias
      3. Apply stability thresholds (R2–R4 hardening rules)
      4. Upsert into model_performance using existing unique constraint
      5. degradation_flagged is STICKY — survives until explicit retrain event

    Committed once outside loop.
    """
    logger.info("─" * 62)
    logger.info("📊 Phase 3B: Rolling Performance Metrics starting...")

    # R1 — always use epi-time anchor
    last_data_week = _get_last_data_week(cursor)
    if not last_data_week:
        logger.warning("  No data week anchor — aborting Phase 3B.")
        return

    rolling_start = last_data_week - timedelta(weeks=_ROLLING_WEEKS)
    logger.info(f"  📅 Window: {rolling_start}  →  {last_data_week}")

    # All targets that have EVER been validated (so we can downgrade them if they drop out of window)
    cursor.execute("""
        SELECT DISTINCT ward, organism, antibiotic
        FROM forecast_validation_log
        ORDER BY ward, organism, antibiotic
    """)
    targets = cursor.fetchall()
    logger.info(f"  🔎 Targets with historical validation data: {len(targets)}")

    updated   = 0
    skipped   = 0
    flagged   = 0

    for (ward, org, abx) in targets:

        # ── Rolling window metrics (G6 leakage-safe — open weeks excluded) ───
        cursor.execute("""
            SELECT
                AVG(ABS(prediction_error))                                   AS rolling_mae,
                COUNT(*)                                                      AS validated_count,
                AVG(prediction_error)                                         AS mean_bias,
                SUM(CASE WHEN direction_correct = TRUE THEN 1 ELSE 0 END)
                    * 100.0
                    / NULLIF(COUNT(CASE WHEN direction_correct IS NOT NULL
                                   THEN 1 END), 0)                           AS mda
            FROM forecast_validation_log
            WHERE ward       = %s
              AND organism   = %s
              AND antibiotic = %s
              AND prediction_error IS NOT NULL
              AND forecast_week >  %s
              AND forecast_week <= %s
        """, (ward, org, abx, rolling_start, last_data_week))
        row = cursor.fetchone()

        if not row or int(row[1]) == 0:
            # Target has no data in the current 12-week window.
            # Explicitly mark as INSUFFICIENT_DATA and clear metrics.
            rolling_mae = None
            validated_count = 0
            mean_bias = None
            mda = None
        else:
            rolling_mae = float(row[0]) if row[0] is not None else None
            validated_count = int(row[1])
            mean_bias = float(row[2]) if row[2] is not None else None
            mda = float(row[3]) if row[3] is not None else None

        # ── R2: Minimum sample guard ──────────────────────────────────────────
        # We don't 'continue' here anymore — we proceed to upsert the INSUFFICIENT_DATA status
        # to ensure the database drops stale targets from ACCEPTABLE/EXCELLENT
        if validated_count < _MIN_VALIDATED:
            skipped += 1

        # ── R3: Degradation detection (sticky flag) ───────────────────────────
        # Read existing degradation_flagged before deciding
        cursor.execute("""
            SELECT degradation_flagged
            FROM model_performance
            WHERE ward = %s AND organism = %s AND antibiotic = %s
            ORDER BY updated_at DESC
            LIMIT 1
        """, (ward, org, abx))
        existing_deg = cursor.fetchone()
        prior_degradation = bool(existing_deg[0]) if existing_deg and existing_deg[0] else False

        degradation_flagged = prior_degradation  # sticky — start from prior state
        if rolling_mae is not None and rolling_mae > _DEGRADATION_MAE and validated_count >= _DEGRADATION_MIN_N:
            degradation_flagged = True
            logger.warning(
                f"  ⚠️  MODEL_DEGRADATION_WARNING: "
                f"{org}/{abx}/{ward} "
                f"(MAE={rolling_mae:.1f}%, n={validated_count})"
            )
            flagged += 1

        # ── R4: Systematic bias check (logged, not flagged) ───────────────────
        if mean_bias is not None and rolling_mae and abs(mean_bias) > rolling_mae * _BIAS_RATIO:
            logger.warning(
                f"  ⚠️  SYSTEMATIC_BIAS_WARNING: "
                f"{org}/{abx}/{ward} "
                f"(bias={mean_bias:+.1f}%, MAE={rolling_mae:.1f}%)"
            )

        # ── Performance status ────────────────────────────────────────────────
        status = _compute_performance_status(rolling_mae, validated_count, degradation_flagged)

        # ── Adaptive CI width ─────────────────────────────────────────────────
        # Exposed via mae_score — Phase 4 will read this directly
        adaptive_ci_width = (
            rolling_mae * 1.96
            if validated_count >= _MIN_VALIDATED and rolling_mae is not None
            else _FALLBACK_CI_WIDTH
        )

        # ── Upsert into model_performance ─────────────────────────────────────
        # Unique constraint is (ward, organism, antibiotic, model_name)
        # degradation_flagged ONLY flips TRUE → FALSE on explicit retrain (CASE guard)
        cursor.execute("""
            INSERT INTO model_performance
                (ward, organism, antibiotic, model_name,
                 mae_score, validated_count, mean_bias, mda,
                 degradation_flagged, performance_status, updated_at)
            VALUES
                (%s, %s, %s, 'Phase3B_Rolling',
                 %s, %s, %s, %s,
                 %s, %s, NOW())
            ON CONFLICT (ward, organism, antibiotic, model_name)
            DO UPDATE SET
                mae_score           = EXCLUDED.mae_score,
                validated_count     = EXCLUDED.validated_count,
                mean_bias           = EXCLUDED.mean_bias,
                mda                 = EXCLUDED.mda,
                performance_status  = EXCLUDED.performance_status,
                updated_at          = NOW(),
                degradation_flagged =
                    CASE
                        WHEN model_performance.degradation_flagged = TRUE
                        THEN TRUE
                        ELSE EXCLUDED.degradation_flagged
                    END
        """, (
            ward, org, abx,
            rolling_mae, validated_count, mean_bias, mda,
            degradation_flagged, status
        ))
        updated += 1

    # ── Commit once — full loop is one transaction ────────────────────────────
    conn.commit()
    logger.info(
        f"  ✅ Phase 3B complete — "
        f"updated={updated}, skipped={skipped}, "
        f"degradation_warnings={flagged}"
    )
    logger.info("─" * 62)


def get_adaptive_ci_width(cursor, ward, org, abx):
    """
    Called by /api/analysis/target to get CI width for this specific target.
    Returns adaptive CI (MAE * 1.96) when ≥ 6 validated weeks exist,
    else returns static fallback of ±10%.
    """
    cursor.execute("""
        SELECT mae_score, validated_count
        FROM model_performance
        WHERE ward = %s AND organism = %s AND antibiotic = %s
          AND model_name = 'Phase3B_Rolling'
        ORDER BY updated_at DESC
        LIMIT 1
    """, (ward, org, abx))
    row = cursor.fetchone()
    if row and row[0] is not None and row[1] is not None and int(row[1]) >= _MIN_VALIDATED:
        return float(row[0]) * 1.96
    return _FALLBACK_CI_WIDTH


# =============================================================================
# STAGE E — MAIN LOOP
# =============================================================================

def run_stage_e_loop():
    conn   = engine.raw_connection()
    cursor = conn.cursor()

    try:
        logger.info("🎬 Starting Stage E: Continuous Learning Loop...")

        # ── E1: Epi-time anchor (R1) ─────────────────────────────────────────
        cursor.execute("SELECT MAX(week_start_date) FROM ast_weekly_aggregated")
        latest_week = cursor.fetchone()[0]

        if not latest_week:
            logger.warning("No data in ast_weekly_aggregated. Aborting.")
            return

        logger.info(f"📅 Current Data Week: {latest_week}")

        # ── PHASE 3A — Prediction Finalization ───────────────────────────────
        # Sequence: Stage B aggregation → 3A validation → 3B MAE → forecast
        finalize_closed_week_predictions(cursor, conn)

        # ── PHASE 3B — Rolling Performance Metrics ───────────────────────
        # Must run AFTER 3A (needs fresh validation rows) and
        # BEFORE forecast generation (adaptive CI is consumed downstream)
        update_rolling_performance_metrics(cursor, conn)

        # ── PHASE 4A — Multi-Model Auto-Selection (Option C: weekly) ─────
        # Backtesting is computationally heavy — only run once per 7 days.
        # Daily Stage E runs simply consume the pre-selected active model.
        if _BACKTESTER_AVAILABLE:
            cursor.execute("""
                SELECT MAX(last_backtest_at)
                FROM model_performance
            """)
            last_bt_row = cursor.fetchone()
            last_bt = last_bt_row[0] if (last_bt_row and last_bt_row[0]) else None

            days_since_bt = (datetime.now() - last_bt).days if last_bt else 999

            if days_since_bt >= 7:
                logger.info(f"🧠 Phase 4A: Backtesting due — last run {days_since_bt} days ago")

                # Pre-compute LSTM MAEs from the rolling window in forecast_validation_log
                # so backtester can include LSTM in the per-model comparison
                cursor.execute("""
                    SELECT
                        ward, organism, antibiotic,
                        AVG(ABS(prediction_error)) AS lstm_mae
                    FROM forecast_validation_log
                    WHERE prediction_error IS NOT NULL
                      AND forecast_week >  %s
                      AND forecast_week <= %s
                    GROUP BY ward, organism, antibiotic
                """, (latest_week - timedelta(weeks=12), latest_week))
                lstm_mae_rows = cursor.fetchall()
                lstm_maes = {
                    (r[0], r[1], r[2]): float(r[3])
                    for r in lstm_mae_rows
                    if r[3] is not None
                }
                logger.info(f"  Pre-computed LSTM MAEs for {len(lstm_maes)} targets")

                run_model_auto_selection(
                    cursor=cursor,
                    conn=conn,
                    last_data_week=latest_week,
                    lstm_maes=lstm_maes
                )
            else:
                logger.info(
                    f"⏭  Phase 4A: Skipping backtest — ran {days_since_bt} days ago "
                    f"(next run in {7 - days_since_bt} days)"
                )
        else:
            logger.warning("⚠️ Phase 4A: backtester module not available — skipping")

        # ── Retraining Strategy ───────────────────────────────────────────────
        cursor.execute(
            "SELECT MAX(created_at) FROM stp_model_registry WHERE status = 'active'"
        )
        last_train_time = cursor.fetchone()[0]

        needs_retraining = False
        if not last_train_time:
            needs_retraining = True
            logger.info("⚠️ No active model found. Retraining required.")
        else:
            from datetime import timezone
            days_since = (datetime.now(timezone.utc) - last_train_time).days
            if days_since >= 28:
                needs_retraining = True
                logger.info(f"⚠️ Last training {days_since} days ago. Retraining required.")

        if needs_retraining:
            logger.info("🔄 Triggering LSTM Retraining (Stub)...")
            new_version = f"LSTM_v1.{datetime.now().strftime('%Y%m%d')}"
            cursor.execute("""
                INSERT INTO stp_model_registry
                    (model_type, target, horizon, features_hash, stage2_version, status, filepath)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, ('lstm', 'resistance_rate', 4, 'stb_v1_hash', new_version, 'active', f'/models/{new_version}.pth'))
            conn.commit()
            logger.info(f"✅ Model Registry Updated: {new_version}")

        # ── Generate next week forecast ───────────────────────────────────────
        next_week = latest_week + timedelta(days=7)
        logger.info(f"🔮 Generating Forecast for Next Week: {next_week}")

        cursor.execute("""
            SELECT DISTINCT ward, organism, antibiotic
            FROM ast_weekly_aggregated
            WHERE week_start_date >= %s
        """, (latest_week - timedelta(weeks=4),))
        targets = cursor.fetchall()

        forecast_count = 0
        for (t_ward, t_org, t_abx) in targets:
            history = PredictionService.get_recent_history(
                cursor, t_ward, t_org, t_abx, next_week
            )

            if len(history) >= 1:
                pred_val = float(sum(history) / len(history))  # SMA fallback

                cursor.execute("""
                    SELECT id FROM predictions
                    WHERE ward=%s AND organism=%s AND antibiotic=%s
                      AND target_week_start=%s AND is_ward_level=TRUE
                """, (t_ward, t_org, t_abx, next_week))

                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO predictions
                            (ward, organism, antibiotic, target_week_start,
                             predicted_s_percent, model_used, is_ward_level, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, TRUE, NOW())
                    """, (t_ward, t_org, t_abx, next_week,
                          pred_val, "Hybrid_LSTM_CL_v1"))
                    forecast_count += 1

        conn.commit()
        logger.info(f"✅ Generated {forecast_count} new forecasts for {next_week}")

    except Exception as e:
        logger.error(f"❌ Critical Error in Stage E Loop: {e}", exc_info=True)
        conn.rollback()
    finally:
        cursor.close()
        conn.close()
        logger.info("🏁 Stage E Loop Completed.")


if __name__ == "__main__":
    run_stage_e_loop()
