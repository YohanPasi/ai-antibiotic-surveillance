
# STP Stage 5 Methodology: Operational Governance
**Version**: 1.0.0
**Governance**: M56-M75 (19 Policies)
**Status**: Implemented & Verified

## 1. Overview
Stage 5 transforms the validated models into a **safe, monitored, and governed operational system**. It provides the "Institute-Level" controls required for real-world deployment.

## 2. Governance Framework (M56-M75)

| ID | Policy | Implementation |
| :--- | :--- | :--- |
| **M56-M59** | **Continuous Monitoring** | `stp_drift_monitor.py` tracks PSI and Prediction Drift. |
| **M60** | **Alert Fatigue** | `stp_alert_manager.py` deduplicates alerts (24h window). |
| **M61** | **Human Loop** | API (`POST /alerts/{id}/review`) for Acknowledgement. |
| **M62** | **Audit Trail** | `stp_prediction_audit_log` records every inference event. |
| **M63** | **Kill Switch** | `stp_model_governance.py` allows immediate deactivation. |
| **M66** | **Traceability** | Logs link Prediction -> Model -> Dataset Hash. |
| **M67** | **No Silent Updates** | Inference engine loads only `ACTIVE` or `SHADOW` models. |
| **M71** | **Data Retention** | `retention_expires_at` column in logs (24 months). |
| **M72** | **Incident Escalation** | Critical drift (>0.2 PSI) creates `stp_incident_events`. |
| **M73** | **Shadow Mode** | Models can run in `SHADOW` mode (logging only, no alerts). |
| **M74** | **Approvals** | Governance actions are signed in `stp_governance_approvals`. |
| **M75** | **System Health** | `GET /monitoring/system-health` tracks job success. |

## 3. Architecture

### A. Database (Operational Schema)
-   `stp_live_predictions`: The hot storage for dashboards.
-   `stp_prediction_audit_log`: The immutable compliance ledger.
-   `stp_alert_events`: Active risks needing attention.
-   `stp_incident_events`: System-level issues (Drift/Failure).
-   `stp_model_lifecycle_events`: History of activations/retirements.

### B. Opeational Engines (`api/ops_engine/`)
-   **Inference**: `stp_live_inference.py` (The Runner).
-   **Drift**: `stp_drift_monitor.py` (The Watchdog).
-   **Alerts**: `stp_alert_manager.py` (The Filter).
-   **Governance**: `stp_model_governance.py` (The Controller).

### C. API (`api/routers/stp_stage_5.py`)
-   Monitoring Dashboards (Drift, Health).
-   Alert Management (List, Review).
-   Control Plane (Deactivate Model).
-   **M70**: All endpoints include "Surveillance Only" disclaimer.

## 4. Verification
Automated Unit Tests (`tests/test_stp_stage_5.py`) PASSED:
-   **M60**: Confirmed Alert Deduplication logic.
-   **M58/M72**: Confirmed PSI Calculation and Incident Triggering.
-   **M63**: Confirmed Model Deactivation logic.
