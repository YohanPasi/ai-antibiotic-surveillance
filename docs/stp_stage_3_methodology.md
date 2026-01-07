
# STP Stage 3 Methodology: Predictive Modeling & Intelligence
**Version**: 1.0.0
**Governance**: M23-M40 (18 Policies)
**Status**: Implemented & Verified

## 1. Overview
Stage 3 builds the **Predictive Intelligence Layer**, using frozen Stage 2 features to forecast resistance risks and detect emerging epidemiological signals.

## 2. Governance Policies (Implemented)
Strict adherence to M23-M40 ensures clinical safety and statistical rigor.

| ID | Policy | Implementation |
| :--- | :--- | :--- |
| **M23** | Frozen Inputs | `stp_preprocessing.load_frozen_features` rejects non-frozen Stage 2 data. |
| **M24** | Temporal Validation | `stp_forecasting.train_with_temporal_cv` uses time-ordered splits (no shuffling). |
| **M25** | Horizon Transparency | API returns `forecast_horizon` metadata for every prediction. |
| **M26** | Imbalance Handling | `stp_preprocessing.handle_imbalance` calculates class weights. |
| **M27** | Interpretability | SHAP values calculated for every model artifact. |
| **M28** | Aggregation Only | Outputs restricted to Ward-Organism level (no patient identifiers). |
| **M29** | Model Freeze | Models serialized to `stp_model_registry` with version UUIDs. |
| **M30** | Non-Clinical Disclaimer | All API responses include "NOT FOR CLINICAL DIAGNOSIS" warning. |
| **M31** | Label Integrity | Targets derived strictly from future weeks ($T+h$). Leakage checked. |
| **M32** | Baseline Comparison | ML models evaluated against Naive/Rolling Mean benchmarks. |
| **M33** | Uncertainty Bounds | Predictions include bootstrap/quantile intervals. |
| **M34** | Alert Escalation | Risk Levels (L/M/H) determined by confidence & persistence. |
| **M35** | Drift Monitoring | PSI (Population Stability Index) calculated daily. |
| **M36** | Fairness Audit | Performance stratified by ward to detect location bias. |
| **M37** | Human-in-Loop | Alerts flagged `new` until explicitly `reviewed` by human officer. |
| **M38** | Calibration | Isotonic calibration required. Brier score reported. |
| **M39** | Threshold Optimization | Thresholds selected to maximize Sensitivity at fixed NPV (e.g., 0.95). |
| **M40** | Horizon Consistency | $T+1$ forecasts evaluated only against $T+1$ outcomes. |

## 3. Architecture

### 3.1 Engines (`api/modeling_engine/`)
-   **Forecasting**: XGBoost/LogReg with Temporal CV.
-   **Signal Detection**: CUSUM and Bayesian Change Point detection.
-   **Labels**: Future window generation with strict date checks.

### 3.2 Database Schema
-   `stp_model_registry`: Versioned model artifacts.
-   `stp_model_predictions`: Probabilistic forecasts with CI.
-   `stp_early_warnings`: Statistical anomalies.

## 4. Verification Check
Automated unit tests (`tests/test_stp_stage_3.py`) confirmed:
-   M31: No leakage of future labels into past features.
-   M23: Rejection of unfrozen inputs.
-   M24: Temporal split order validity.
