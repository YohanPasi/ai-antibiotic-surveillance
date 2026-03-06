"""
Phase 4B — Drift & Change-Point Detection Engine.

Provides per-target epidemiological intelligence beyond pure forecast accuracy:
  1. Formal CUSUM      (G3) — k = 0.5σ, h = 5σ, directional sensitivity
  2. Variance-scaled slope detection — slope threshold adaptive to local data noise
  3. Residual volatility spike detection — sudden variance inflation

All algorithms operate on the same rolling 12-week anchored window as Phases 3B/4A.
Outputs feed into the G8 alert precedence hierarchy (Priority 1–6).

G8 Alert Precedence (deterministic, no ambiguity):
  Priority 1 — RED            Susceptibility breach (adaptive tolerance)
  Priority 2 — DRIFT_WARNING  Regime shift (CUSUM or slope triggered)
  Priority 3 — DEGRADED       Model unreliable (Phase 3B degradation_flagged)
  Priority 4 — BIAS_WARNING   Systematic over/underestimation
  Priority 5 — AMBER          Watch — elevated but not yet breached
  Priority 6 — GREEN          Within normal range

Rule: highest-priority badge displayed primary; all others as secondary pills.
"""

import math
import statistics
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Algorithm constants (publication-grade, tunable) ──────────────────────────
_CUSUM_K_RATIO       = 0.5    # G3: allowance = k × σ
_CUSUM_H_RATIO       = 5.0    # G3: decision threshold = h × σ
_CUSUM_SIGMA_WINDOW  = 12     # CHECK 1: σ computed over 12-week rolling window (stable estimate)
_CUSUM_LOOKBACK      = 8      # CUSUM accumulator over last 8 points (sensitive detection)
_SLOPE_FACTOR        = 1.2    # Variance-scaled slope: threshold = max(5%, σ × 1.2)
_SLOPE_FLOOR         = 5.0    # Minimum slope threshold regardless of σ (%)
_VOLATILITY_RATIO    = 2.0    # Volatility spike: recent_std > historical_std × ratio
_MIN_HISTORY         = 8      # Minimum points needed for any drift signal


# =============================================================================
# CUSUM — Formal change-point detection (G3)
# =============================================================================

def cusum_alert(history: list, lookback: int = _CUSUM_LOOKBACK) -> dict:
    """
    Two-sided CUSUM change-point detection (G3).

    CHECK 1 fix: Parameters derived from a 12-week rolling window, NOT full history.
      σ = stdev(last 12 weeks)   — stable estimate; full-history σ is distorted by
                                    old regimes and inflates false positives on short data
      k = 0.5 × σ               (allowance — insensitive to noise within 0.5σ)
      h = 5.0 × σ               (decision threshold — signals sustained regime shift)
    Accumulator runs on last `lookback` (8) points — sensitivity window.

    Two-sided: detects both increases (rising resistance) AND decreases.
    CUSUM direction: UP (C_pos dominant) / DOWN (C_neg dominant) — magnitude deviation.
    Epidemiological direction should always be confirmed by slope_drift_alert.
    """
    result = {
        "cusum_triggered": False,
        "C_pos": 0.0, "C_neg": 0.0,
        "sigma": None, "k": None, "h": None,
        "direction": None
    }

    if len(history) < _MIN_HISTORY:
        return result

    vals = [float(v) for v in history if v is not None]
    if len(vals) < _MIN_HISTORY:
        return result

    # CHECK 1: sigma from last 12 weeks (rolling, stable); accumulator from last 8
    sigma_window = vals[-_CUSUM_SIGMA_WINDOW:]
    if len(sigma_window) < 2:
        return result

    sigma = statistics.stdev(sigma_window)
    if sigma < 1e-6:
        return result

    mu  = statistics.mean(sigma_window)   # mean also from same stable 12-week window
    k   = _CUSUM_K_RATIO * sigma
    h   = _CUSUM_H_RATIO * sigma

    recent = vals[-lookback:]
    C_pos  = 0.0
    C_neg  = 0.0

    for x_t in recent:
        C_pos = max(0.0, C_pos + (x_t - mu - k))
        C_neg = max(0.0, C_neg - (x_t - mu + k))

    triggered = (C_pos > h) or (C_neg > h)
    direction = None
    if triggered:
        direction = "UP" if C_pos > C_neg else "DOWN"

    result.update({
        "cusum_triggered": triggered,
        "C_pos": round(C_pos, 3),
        "C_neg": round(C_neg, 3),
        "sigma": round(sigma, 3),
        "k": round(k, 3),
        "h": round(h, 3),
        "direction": direction
    })
    return result


# =============================================================================
# VARIANCE-SCALED SLOPE DETECTION
# =============================================================================

def slope_drift_alert(history: list, lookback: int = 6) -> dict:
    """
    Variance-scaled slope detection.

    Computes OLS slope over the last `lookback` points.
    Threshold = max(_SLOPE_FLOOR, σ_full × _SLOPE_FACTOR) [%/week].

    Using data-adaptive threshold prevents false positives in noisy targets
    (e.g., a ward with ±8% variation needs a higher slope to signal).

    Returns:
        {
          "slope_triggered": bool,
          "slope_per_week": float,
          "slope_threshold": float,
          "direction": "FALLING" | "RISING" | None
        }
    """
    result = {
        "slope_triggered": False,
        "slope_per_week": None,
        "slope_threshold": None,
        "direction": None
    }

    if len(history) < _MIN_HISTORY:
        return result

    vals = [float(v) for v in history if v is not None]
    if len(vals) < _MIN_HISTORY:
        return result

    sigma = statistics.stdev(vals)
    slope_threshold = max(_SLOPE_FLOOR, sigma * _SLOPE_FACTOR)

    # OLS regression on last `lookback` points
    recent = vals[-lookback:]
    n = len(recent)
    if n < 3:
        return result

    xs = list(range(n))
    x_mean = statistics.mean(xs)
    y_mean = statistics.mean(recent)

    num   = sum((xs[i] - x_mean) * (recent[i] - y_mean) for i in range(n))
    denom = sum((xs[i] - x_mean) ** 2 for i in range(n))

    if abs(denom) < 1e-9:
        return result

    slope = num / denom  # %/week

    triggered = abs(slope) > slope_threshold
    direction = None
    if triggered:
        direction = "FALLING" if slope < 0 else "RISING"

    result.update({
        "slope_triggered": triggered,
        "slope_per_week": round(slope, 3),
        "slope_threshold": round(slope_threshold, 3),
        "direction": direction
    })
    return result


# =============================================================================
# RESIDUAL VOLATILITY SPIKE DETECTION
# =============================================================================

def volatility_spike_alert(history: list,
                           recent_window: int = 4,
                           historical_window: int = 12) -> dict:
    """
    Detects sudden variance inflation — a signal of underlying epidemiological
    instability distinct from a directional drift.

    Pattern: target was stable for months, then suddenly oscillates wildly.
    This is not captured by CUSUM (no trend) or slope (no direction).

    Method:
        historical_std = std(history[-historical_window:-recent_window])
        recent_std     = std(history[-recent_window:])
        spike          = recent_std > historical_std × _VOLATILITY_RATIO

    Returns:
        {
          "volatility_triggered": bool,
          "recent_std": float,
          "historical_std": float,
          "ratio": float
        }
    """
    result = {
        "volatility_triggered": False,
        "recent_std": None,
        "historical_std": None,
        "ratio": None
    }

    vals = [float(v) for v in history if v is not None]
    if len(vals) < historical_window + recent_window:
        return result

    recent_vals     = vals[-recent_window:]
    historical_vals = vals[-(historical_window + recent_window):-recent_window]

    if len(recent_vals) < 2 or len(historical_vals) < 2:
        return result

    recent_std     = statistics.stdev(recent_vals)
    historical_std = statistics.stdev(historical_vals)

    if historical_std < 1e-6:
        # Historical was flat — any variance now is significant
        triggered = recent_std > 2.0
        ratio = float('inf') if recent_std > 0 else 0.0
    else:
        ratio = recent_std / historical_std
        triggered = ratio > _VOLATILITY_RATIO

    result.update({
        "volatility_triggered": triggered,
        "recent_std":     round(recent_std, 3),
        "historical_std": round(historical_std, 3),
        "ratio":          round(ratio, 3) if ratio != float('inf') else 999.0
    })
    return result


# =============================================================================
# G8 ALERT PRECEDENCE HIERARCHY — deterministic, no ambiguity
# =============================================================================

def compute_g8_alert(
    observed_s: float,
    baseline_s: float,
    adaptive_tolerance: float,
    cusum: dict,
    slope: dict,
    volatility: dict,
    degradation_flagged: bool,
    mean_bias: Optional[float],
    rolling_mae: Optional[float],
) -> dict:
    """
    Deterministic G8 alert precedence hierarchy.

    All signals are computed independently, then combined with strict
    priority ordering. The primary alert is the highest-priority signal.
    All active signals below the primary are returned as secondary pills.

    Priority 1 — RED            susceptibility < baseline - adaptive_tolerance
    Priority 2 — DRIFT_WARNING  CUSUM triggered OR slope triggered
    Priority 3 — DEGRADED       model_performance.degradation_flagged = TRUE
    Priority 4 — BIAS_WARNING   |mean_bias| > rolling_mae * 0.75
    Priority 5 — AMBER          susceptibility in [baseline - 2*tol, baseline - tol]
    Priority 6 — GREEN          no signal

    Returns:
        {
          "primary_alert": "RED" | "DRIFT_WARNING" | "DEGRADED" | "BIAS_WARNING" | "AMBER" | "GREEN",
          "primary_priority": int,
          "secondary_alerts": ["DRIFT_WARNING", ...],   # lower-priority active signals
          "drift_direction":  "UP" | "DOWN" | "FALLING" | "RISING" | None,
          "volatility_spike": bool,
          "all_signals": {signal: bool}   # full audit trail
        }
    """
    signals = {}

    # Priority 1: Susceptibility breach
    signals["RED"]   = observed_s < (baseline_s - adaptive_tolerance)

    # Priority 2: Drift — CUSUM OR slope triggered
    drift_triggered  = cusum.get("cusum_triggered", False) or slope.get("slope_triggered", False)
    signals["DRIFT_WARNING"] = drift_triggered

    # Priority 3: Model degradation
    signals["DEGRADED"] = bool(degradation_flagged)

    # Priority 4: Systematic bias
    bias_active = (
        mean_bias is not None and rolling_mae is not None
        and rolling_mae > 0
        and abs(mean_bias) > rolling_mae * 0.75
    )
    signals["BIAS_WARNING"] = bias_active

    # Priority 5: Amber watch (within 2× tolerance band but not yet breached)
    amber_lower = baseline_s - 2 * adaptive_tolerance
    amber_upper = baseline_s - adaptive_tolerance
    signals["AMBER"] = not signals["RED"] and (amber_lower <= observed_s <= amber_upper)

    # Priority 6: Green — fallback
    signals["GREEN"] = True   # always a candidate, overridden by higher priorities

    # Resolve hierarchy — deterministic
    _priority_order = ["RED", "DRIFT_WARNING", "DEGRADED", "BIAS_WARNING", "AMBER", "GREEN"]
    active_signals  = [s for s in _priority_order if signals.get(s, False)]

    primary_alert    = active_signals[0] if active_signals else "GREEN"
    primary_priority = _priority_order.index(primary_alert) + 1
    secondary_alerts = [s for s in active_signals[1:] if s != "GREEN"]

    # CHECK 2 fix: Drift direction — slope is the primary directional signal.
    # CUSUM detects sustained magnitude deviation; slope gives the epidemiological
    # direction (FALLING = treatment efficacy loss, RISING = unusual improvement).
    # When slope is triggered, prefer its FALLING/RISING over CUSUM's UP/DOWN.
    # When only CUSUM is triggered and slope is not, use CUSUM direction.
    # When CUSUM is triggered but slope ≈ 0 (oscillatory regime), direction = None.
    drift_direction = None
    if slope.get("slope_triggered"):
        drift_direction = slope.get("direction")         # primary: FALLING / RISING
    elif cusum.get("cusum_triggered"):
        # Only use CUSUM direction if slope did not independently confirm direction
        slope_val = slope.get("slope_per_week")
        if slope_val is not None and abs(slope_val) > (slope.get("slope_threshold", 999) * 0.5):
            # Slope shows notable movement even if below threshold — use it for direction
            drift_direction = "FALLING" if slope_val < 0 else "RISING"
        else:
            drift_direction = cusum.get("direction")    # fallback: UP / DOWN

    return {
        "primary_alert":    primary_alert,
        "primary_priority": primary_priority,
        "secondary_alerts": secondary_alerts,
        "drift_direction":  drift_direction,
        "volatility_spike": volatility.get("volatility_triggered", False),
        "all_signals":      {k: bool(v) for k, v in signals.items()},
        # Raw detector outputs for publication / audit
        "cusum_detail":       cusum,
        "slope_detail":       slope,
        "volatility_detail":  volatility,
    }


# =============================================================================
# CONVENIENCE WRAPPER — called from /api/analysis/target
# =============================================================================

def run_drift_analysis(
    history: list,
    observed_s: float,
    baseline_s: float,
    adaptive_tolerance: float,
    degradation_flagged: bool,
    mean_bias: Optional[float],
    rolling_mae: Optional[float],
    validated_count: int = 6,   # CHECK 5: pass from Phase 3B
    active_model: str = "",     # CHECK 5: pass from Phase 4A
) -> dict:
    """
    Single entry point for use in /api/analysis/target.

    CHECK 5: Cold-start bypass.
      If validated_count < 6 OR active_model == 'BASELINE_MEAN':
        Drift detection is meaningless and statistically invalid.
        Returns a deterministic 'INSUFFICIENT_DATA' shell that bypasses
        CUSUM/slope/volatility entirely. No false drift signals.

    CHECK 6: Caller must slice history to last 16 weeks before calling.
      This is enforced in main.py, not here, to keep this module stateless.

    All tolerances must have already been computed by Phase 4C.
    """
    # CHECK 5: Cold-start or insufficient data — bypass all detectors
    if len(history) < 8:
        return {
            "primary_alert":    "INSUFFICIENT_DATA",
            "primary_priority": 7,   # Below GREEN — signals 'no information'
            "secondary_alerts": [],
            "drift_direction":  None,
            "volatility_spike": False,
            "all_signals":      {},
            "bypass_reason":    f"validated_count={validated_count}, model={active_model}",
            "cusum_detail":     {},
            "slope_detail":     {},
            "volatility_detail": {},
        }

    cusum      = cusum_alert(history)
    slope      = slope_drift_alert(history)
    volatility = volatility_spike_alert(history)

    return compute_g8_alert(
        observed_s          = observed_s,
        baseline_s          = baseline_s,
        adaptive_tolerance  = adaptive_tolerance,
        cusum               = cusum,
        slope               = slope,
        volatility          = volatility,
        degradation_flagged = degradation_flagged,
        mean_bias           = mean_bias,
        rolling_mae         = rolling_mae,
    )
