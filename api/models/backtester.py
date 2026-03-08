"""
Phase 4A — Walk-Forward Backtesting Engine.

Provides:
  - Four model classes: BaselineMean, SMA4, ARIMA, ETS
  - walk_forward_mae()          — per-model MAE over a history series
  - run_model_auto_selection()  — eligibility cascade + full backtest + hysteresis
  - get_active_model()          — reads active model for a target (for forecast consumption)

Hardening invariants (CHECK 1–6):
  CHECK 1: Partial unique index idx_one_active_model enforces exactly-one-active at DB level
  CHECK 2: model_results is filtered of None MAEs before min() selection; fallback to SMA4
  CHECK 3: Cold-start targets bypass adaptive CI and drift entirely — documented in
           _ensure_active_model() and the Stage E forecast block must check model_name
  CHECK 4: LSTM is NOT re-trained per walk-forward window (LSTM retraining requires a GPU
           and 10k+ samples). Instead, its rolling MAE from forecast_validation_log is used
           as a fair empirical comparison over the same rolling window used by the others.
           This is methodologically equivalent as long as LSTM validation was truly out-of-sample,
           which is guaranteed by the Phase 3A closed-week guard (forecast_week <= last_data_week).
           This limitation is documented here for transparency in any publication Methods section.
  CHECK 5: Degradation policy — switching IS allowed when degradation_flagged = TRUE.
           Rationale: if the model is degraded, SWITCHING to a better model is beneficial.
           Freezing would prevent recovery. Degradation flag clears ONLY on explicit retrain.
           This is explicitly logged in model_switch_log.reason.
  CHECK 6: per-target weekly schedule guard — last_backtest_at checked per (ward,org,abx),
           not globally. Targets run independently; one recently-backtested target
           does not prevent others from running.

Design decisions:
  * All backtesting uses strict walk-forward (no look-ahead)
  * Minimum training window = 12 weeks (matches G1)
  * ARIMA / ETS gracefully degrade to SMA4 if statsmodels is unavailable
  * Global weekly guard is checked in stage_e BEFORE calling this function;
    that is a coarse "skip" guard. Per-target guard here is the fine-grained one.
"""

import logging
import statistics
from datetime import datetime, date, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# ── Hysteresis threshold (R5) ─────────────────────────────────────────────────
_SWITCH_HYSTERESIS    = 1.0     # Δ MAE must exceed this % to justify a switch
_MIN_BACKTEST_WINDOW  = 12      # Minimum training weeks for walk-forward
_COLD_START_WEEKS     = 4       # G7: < 4 weeks → BASELINE_MEAN, no model switching
_SPARSE_WEEKS         = 20      # G4: < 20 weeks or < 8 validated → SMA4
_SPARSE_VALIDATED     = 8       # G4: minimum validated count for full backtest
_BACKTEST_INTERVAL    = 7       # Days between per-target backtest runs (CHECK 6)


# =============================================================================
# MODEL CLASSES — each wraps a forecasting algorithm
# =============================================================================

class BaselineMeanModel:
    """
    G7: Cold-start fallback. Returns the mean of training data.

    CHECK 3: When this model is active, the forecast endpoint must NOT
    apply adaptive CI (it must use the static ±10% fallback).
    Stage E checks model_name == 'BASELINE_MEAN' to enforce this.
    """
    name = "BASELINE_MEAN"

    def __init__(self):
        self._mean = None

    def fit(self, train):
        self._mean = statistics.mean(train) if train else 0.0
        return self

    def predict(self, steps=1):
        return [self._mean] * steps


class SMA4Model:
    """Simple 4-week moving average. Sparse target fallback (G4)."""
    name = "SMA4"

    def __init__(self):
        self._last4 = []

    def fit(self, train):
        self._last4 = list(train[-4:])
        return self

    def predict(self, steps=1):
        if not self._last4:
            return [0.0] * steps
        val = statistics.mean(self._last4)
        return [val] * steps


class ARIMAModel:
    """ARIMA(1,1,1) — requires statsmodels. Falls back to SMA4 on import error."""
    name = "ARIMA"

    def __init__(self):
        self._fitted = None
        self._fallback = SMA4Model()
        self._use_fallback = False

    def fit(self, train):
        if len(train) < 8:
            self._use_fallback = True
            self._fallback.fit(train)
            return self
        try:
            from statsmodels.tsa.arima.model import ARIMA as SM_ARIMA
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = SM_ARIMA(train, order=(1, 1, 1))
                self._fitted = model.fit()
            self._use_fallback = False
        except Exception as e:
            logger.debug(f"ARIMA fit failed ({e}), falling back to SMA4")
            self._use_fallback = True
            self._fallback.fit(train)
        return self

    def predict(self, steps=1):
        if self._use_fallback:
            return self._fallback.predict(steps)
        try:
            fc = self._fitted.forecast(steps=steps)
            return list(fc)
        except Exception:
            return self._fallback.predict(steps)


class ETSModel:
    """Exponential Smoothing (simple) — requires statsmodels. Falls back to SMA4."""
    name = "ETS"

    def __init__(self):
        self._fitted = None
        self._fallback = SMA4Model()
        self._use_fallback = False

    def fit(self, train):
        if len(train) < 4:
            self._use_fallback = True
            self._fallback.fit(train)
            return self
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model = ExponentialSmoothing(
                    train,
                    trend=None,
                    seasonal=None,
                    initialization_method="estimated"
                )
                self._fitted = model.fit(optimized=True)
            self._use_fallback = False
        except Exception as e:
            logger.debug(f"ETS fit failed ({e}), falling back to SMA4")
            self._use_fallback = True
            self._fallback.fit(train)
        return self

    def predict(self, steps=1):
        if self._use_fallback:
            return self._fallback.predict(steps)
        try:
            fc = self._fitted.forecast(steps=steps)
            return list(fc)
        except Exception:
            return self._fallback.predict(steps)


_ALL_CANDIDATE_MODELS = [SMA4Model, ARIMAModel, ETSModel]
# LSTM is NOT in the walk-forward loop (CHECK 4 — see module docstring).
# Its MAE is supplied externally from forecast_validation_log by stage_e.


# =============================================================================
# WALK-FORWARD BACKTESTER
# =============================================================================

def walk_forward_mae(history: list, model_class, min_window: int = _MIN_BACKTEST_WINDOW) -> Optional[float]:
    """
    Strict walk-forward cross-validation (no look-ahead).

    All models evaluated on IDENTICAL indices (min_window to len(history)-1),
    so all MAE values are directly comparable (CHECK statistical integrity).

    For each time step t from min_window to len(history)-1:
        train     = history[:t]           # expanding window
        actual    = history[t]            # true next value
        predicted = model.fit(train).predict(1)[0]
        error     = |actual - predicted|

    Returns: mean absolute error, or None if < 2 successful folds.
    """
    errors = []

    for t in range(min_window, len(history)):
        train  = [float(v) for v in history[:t]]
        actual = float(history[t])

        try:
            model     = model_class()   # fresh instance each fold — no state leakage
            model.fit(train)
            predicted = model.predict(1)[0]
            errors.append(abs(actual - predicted))
        except Exception as e:
            logger.debug(f"  Backtest step t={t} failed for {model_class.name}: {e}")
            continue

    if len(errors) < 2:
        return None

    return sum(errors) / len(errors)


# =============================================================================
# PHASE 4A MAIN FUNCTION — called from stage_e weekly
# =============================================================================

def run_model_auto_selection(cursor, conn, last_data_week: date, lstm_maes: dict):
    """
    Phase 4A — Multi-Model Auto-Selection Engine.

    Algorithm per target:
      1. Per-target schedule guard   (CHECK 6: last_backtest_at per row)
      2. Cold-start guard            (G7)
      3. Eligibility filter          (G4)
      4. Walk-forward backtest       (SMA4, ARIMA, ETS)
      5. Merge LSTM MAE              (CHECK 4: empirical from validation log)
      6. Filter None MAEs            (CHECK 2)
      7. Hysteresis selection        (R5)
      8. Degradation-aware logging   (CHECK 5: switching allowed, logged)
      9. Persist active model        (DB partial unique index enforces uniqueness)

    Transaction: committed once after all targets.
    """
    logger.info("─" * 62)
    logger.info("🤖 Phase 4A: Multi-Model Auto-Selection starting...")
    logger.info(f"  📅 Epi anchor: {last_data_week}")

    # ── Fetch all candidate targets ────────────────────────────────────────
    cursor.execute("""
        SELECT
            ward,
            organism,
            antibiotic,
            COUNT(*) AS total_weeks,
            array_agg(susceptibility_percent ORDER BY week_start_date) AS history
        FROM ast_weekly_aggregated
        WHERE has_sufficient_data = TRUE
          AND week_start_date <= %s
        GROUP BY ward, organism, antibiotic
        HAVING COUNT(*) >= %s
        ORDER BY ward, organism, antibiotic
    """, (last_data_week, _COLD_START_WEEKS))
    targets = cursor.fetchall()
    logger.info(f"  🔎 Candidates: {len(targets)}")

    switched    = 0
    suppressed  = 0
    cold_start  = 0
    sparse      = 0
    eligible    = 0
    skipped_bt  = 0   # CHECK 6 per-target guard

    for (ward, org, abx, total_weeks, history_raw) in targets:

        history = [float(v) for v in history_raw if v is not None]

        # ── CHECK 6: Per-target weekly schedule guard ─────────────────────
        # Each (ward, org, abx) has its own last_backtest_at. Targets that
        # haven't been backtested yet (NULL) get run on every call.
        cursor.execute("""
            SELECT MAX(last_backtest_at)
            FROM model_performance
            WHERE ward = %s AND organism = %s AND antibiotic = %s
        """, (ward, org, abx))
        last_bt_row = cursor.fetchone()
        last_bt = last_bt_row[0] if (last_bt_row and last_bt_row[0]) else None

        if last_bt is not None:
            days_since = (datetime.now() - last_bt).days
            if days_since < _BACKTEST_INTERVAL:
                skipped_bt += 1
                continue

        # ── G7: Cold-start guard ──────────────────────────────────────────
        if len(history) < _COLD_START_WEEKS:
            _ensure_active_model(cursor, ward, org, abx, "BASELINE_MEAN",
                                 mae=None, last_data_week=last_data_week)
            cold_start += 1
            continue

        # ── G4: Eligibility filter ─────────────────────────────────────────
        validated_count = _get_validated_count(cursor, ward, org, abx, last_data_week)
        if len(history) < _SPARSE_WEEKS or validated_count < _SPARSE_VALIDATED:
            _ensure_active_model(cursor, ward, org, abx, "SMA4",
                                 mae=None, last_data_week=last_data_week)
            sparse += 1
            continue

        eligible += 1

        # ── Walk-forward backtest (SMA4, ARIMA, ETS, identical windows) ───
        model_results = {}

        for model_class in _ALL_CANDIDATE_MODELS:
            mae = walk_forward_mae(history, model_class)
            if mae is not None:
                model_results[model_class.name] = mae
                logger.debug(f"    {model_class.name}: MAE={mae:.2f}%")

        # Merge LSTM MAE (CHECK 4: from empirical rolling validation log)
        lstm_mae = lstm_maes.get((ward, org, abx))
        if lstm_mae is not None:
            model_results["LSTM"] = lstm_mae

        # ── CHECK 2: Filter None MAEs before selection ─────────────────────
        model_results = {k: v for k, v in model_results.items()
                         if v is not None and isinstance(v, (int, float))}
        if not model_results:
            logger.warning(f"  ⚠️  All backtests failed for {org}/{abx}/{ward} — forcing SMA4")
            _ensure_active_model(cursor, ward, org, abx, "SMA4",
                                 mae=None, last_data_week=last_data_week)
            continue

        # ── Persist per-model MAE scores ───────────────────────────────────
        for model_name, mae in model_results.items():
            cursor.execute("""
                INSERT INTO model_performance
                    (ward, organism, antibiotic, model_name, mae_score,
                     last_backtest_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (ward, organism, antibiotic, model_name)
                DO UPDATE SET
                    mae_score        = EXCLUDED.mae_score,
                    last_backtest_at = NOW(),
                    updated_at       = NOW()
            """, (ward, org, abx, model_name, mae))

        # ── Select best model ──────────────────────────────────────────────
        best_model = min(model_results, key=model_results.get)
        best_mae   = model_results[best_model]

        # ── CHECK 5: Degradation-aware switching policy ────────────────────
        # Policy: switching IS allowed when degradation_flagged = TRUE.
        # If a model is degraded, a candidate switch may recover performance.
        # Freezing switching on degraded targets would prevent self-healing.
        # The degradation flag only clears on explicit retraining — not on a switch.
        # When a switch occurs during degradation, reason logs as SWITCH_WHILE_DEGRADED.
        is_degraded = _is_degraded(cursor, ward, org, abx)

        # Get currently active model
        current_model, current_mae = _get_current_active(cursor, ward, org, abx)

        # ── R5: Hysteresis guard ───────────────────────────────────────────
        if current_model is None:
            _set_active_model(cursor, ward, org, abx, best_model)
            logger.info(
                f"  ✅ INITIAL_MODEL: {org}/{abx}/{ward} "
                f"→ {best_model} (MAE={best_mae:.2f}%)"
            )
            switched += 1

        elif best_model != current_model:
            delta = (current_mae or 999.0) - best_mae
            if delta > _SWITCH_HYSTERESIS:
                reason = "SWITCH_WHILE_DEGRADED" if is_degraded else "HYSTERESIS_PASSED"
                _set_active_model(cursor, ward, org, abx, best_model)
                _log_switch(cursor, ward, org, abx,
                            old_model=current_model, new_model=best_model,
                            old_mae=current_mae, new_mae=best_mae,
                            delta=delta, reason=reason,
                            epi_week=last_data_week)
                logger.info(
                    f"  🔄 MODEL_SWITCH [{reason}]: {org}/{abx}/{ward}  "
                    f"{current_model} → {best_model}  "
                    f"MAE: {(current_mae or 0):.2f}% → {best_mae:.2f}%  "
                    f"Δ={delta:.2f}%"
                )
                switched += 1
            else:
                reason = "SUPPRESSED_DEGRADED" if is_degraded else "SUPPRESSED_HYSTERESIS"
                _log_switch(cursor, ward, org, abx,
                            old_model=current_model, new_model=best_model,
                            old_mae=current_mae, new_mae=best_mae,
                            delta=delta, reason=reason,
                            epi_week=last_data_week)
                logger.info(
                    f"  ⏸  MODEL_SWITCH_SUPPRESSED [{reason}]: {org}/{abx}/{ward}  "
                    f"Δ={delta:.2f}% < {_SWITCH_HYSTERESIS}% threshold"
                )
                suppressed += 1
        # else: same model still best — no action

    conn.commit()
    logger.info(
        f"  ✅ Phase 4A complete — "
        f"switched={switched}, suppressed={suppressed}, "
        f"cold_start={cold_start}, sparse={sparse}, "
        f"eligible={eligible}, skipped_per_target_guard={skipped_bt}"
    )
    logger.info("─" * 62)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_validated_count(cursor, ward, org, abx, last_data_week: date) -> int:
    """Rolling 12-week validated count (consistent with Phase 3B G1/G6)."""
    rolling_start = last_data_week - timedelta(weeks=12)
    cursor.execute("""
        SELECT COUNT(*)
        FROM forecast_validation_log
        WHERE ward = %s AND organism = %s AND antibiotic = %s
          AND prediction_error IS NOT NULL
          AND forecast_week >  %s
          AND forecast_week <= %s
    """, (ward, org, abx, rolling_start, last_data_week))
    row = cursor.fetchone()
    return int(row[0]) if row else 0


def _get_current_active(cursor, ward, org, abx):
    """
    Returns (model_name, mae_score) for the currently active model.
    Returns (None, None) if no active model exists yet.
    DB partial unique index guarantees at most one row with is_active=TRUE.
    """
    cursor.execute("""
        SELECT model_name, mae_score
        FROM model_performance
        WHERE ward = %s AND organism = %s AND antibiotic = %s
          AND is_active = TRUE
        LIMIT 1
    """, (ward, org, abx))
    row = cursor.fetchone()
    if row:
        return row[0], (float(row[1]) if row[1] is not None else None)
    return None, None


def _is_degraded(cursor, ward, org, abx) -> bool:
    """
    CHECK 5: Read current degradation state for the target.
    Returns True if any model_performance row carries degradation_flagged=TRUE.
    """
    cursor.execute("""
        SELECT COUNT(*) FROM model_performance
        WHERE ward = %s AND organism = %s AND antibiotic = %s
          AND degradation_flagged = TRUE
    """, (ward, org, abx))
    row = cursor.fetchone()
    return bool(row and row[0] > 0)


def _set_active_model(cursor, ward, org, abx, model_name: str):
    """
    Sets is_active = TRUE for model_name, FALSE for all others for this target.

    Safety: DB-level partial unique index (idx_one_active_model) enforces
    that exactly one row per target can hold is_active=TRUE (CHECK 1).
    We deactivate first, then activate — crash between them leaves zero active
    (safe: get_active_model() returns 'SMA4' default). The index prevents
    two-active-model race conditions entirely.
    """
    cursor.execute("""
        UPDATE model_performance
        SET is_active = FALSE
        WHERE ward = %s AND organism = %s AND antibiotic = %s
    """, (ward, org, abx))

    cursor.execute("""
        UPDATE model_performance
        SET is_active = TRUE, updated_at = NOW()
        WHERE ward = %s AND organism = %s AND antibiotic = %s
          AND model_name = %s
    """, (ward, org, abx, model_name))


def _ensure_active_model(cursor, ward, org, abx, model_name: str,
                         mae, last_data_week: date):
    """
    Cold-start / sparse targets: upsert the assigned model and mark it active.
    CHECK 3: BASELINE_MEAN targets must not receive adaptive CI or drift detection.
             The caller (stage_e forecast block) must check the active model name
             and apply static ±10% CI when model is BASELINE_MEAN.
    """
    cursor.execute("""
        INSERT INTO model_performance
            (ward, organism, antibiotic, model_name, mae_score,
             last_backtest_at, is_active, updated_at)
        VALUES (%s, %s, %s, %s, %s, NOW(), TRUE, NOW())
        ON CONFLICT (ward, organism, antibiotic, model_name)
        DO UPDATE SET
            is_active        = TRUE,
            last_backtest_at = NOW(),
            updated_at       = NOW()
    """, (ward, org, abx, model_name, mae))

    # Deactivate all other models for this target (index enforces one-active)
    cursor.execute("""
        UPDATE model_performance
        SET is_active = FALSE
        WHERE ward = %s AND organism = %s AND antibiotic = %s
          AND model_name != %s
    """, (ward, org, abx, model_name))


def _log_switch(cursor, ward, org, abx, old_model, new_model,
                old_mae, new_mae, delta, reason, epi_week):
    """Write an immutable audit entry to model_switch_log."""
    cursor.execute("""
        INSERT INTO model_switch_log
            (ward, organism, antibiotic, old_model, new_model,
             old_mae, new_mae, delta_mae, reason, epi_week)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (ward, org, abx, old_model, new_model,
          old_mae, new_mae, delta, reason, epi_week))


def get_active_model(cursor, ward: str, org: str, abx: str) -> str:
    """
    Public API — called by Stage E forecast generation.
    Returns the active model name, or 'SMA4' as the safe default.

    CHECK 3: Caller must treat 'BASELINE_MEAN' as a signal to:
      - Use static ±10% CI (not adaptive)
      - Skip drift detection
      - Not contribute to MDA / rolling metrics
    """
    cursor.execute("""
        SELECT model_name
        FROM model_performance
        WHERE ward = %s AND organism = %s AND antibiotic = %s
          AND is_active = TRUE
        LIMIT 1
    """, (ward, org, abx))
    row = cursor.fetchone()
    return row[0] if row else "SMA4"
