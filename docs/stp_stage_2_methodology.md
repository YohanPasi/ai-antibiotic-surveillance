
# STP Stage 2 Methodology: Feature Engineering & Signal Construction
**Version**: 1.0.0
**Governance**: M11-M22
**Status**: Implemented & Verified

## 1. Overview
Stage 2 transforms raw, validated AST data (Stage 1) into epidemiological signals suitable for machine learning and surveillance. This process is strictly governed by 12 policies (M11-M22) ensuring statistical rigor, transparency, and interpretability.

## 2. Governance Policies (Implemented)

| Policy ID | Name | Implementation Detail |
| :--- | :--- | :--- |
| **M11** | Denominator Transparency | All aggregates store `tested_count` alongside rates. |
| **M12** | Minimum Sample Threshold | Rates with $N < 30$ are flagged `is_stable=False`. |
| **M13** | Temporal Firewall | Computation for time $t$ strictly excludes data from $t+k$. |
| **M14** | Feature Immutability | Feature Store snapshots are append-only and versioned. |
| **M15** | Intermediate Handling | 'Intermediate' (I) results are included in the denominator ($N$) but excluded from the numerator ($R$). |
| **M16** | Partial Window Handling | Time windows with incomplete data coverage are flagged `is_partial_window=True`. |
| **M17** | Antibiotic Availability Bias | Antibiotics with $<20\%$ testing coverage in a ward are excluded from diversity indices. |
| **M18** | Signal Interpretability | All signals map to `stp_signal_definitions` metadata. |
| **M19** | Stage 2 Feature Freeze | Explicit versioning (`v2-YYYYMMDD...`) linked to frozen Stage 1 datasets. |
| **M20** | Non-Causal Declaration | API responses include warnings that signals are descriptive associations only. |
| **M21** | Tested Count Definition | $N = S + I + R$. Records with `NA` or `NaN` result are strictly excluded. |
| **M22** | Zero/Suppression Policy | If $N=0 \rightarrow Rate=NULL$. If $N < Threshold \rightarrow is\_stable=False$. |

## 3. Mathematical Definitions

### 3.1 Resistance Rate ($R_{rate}$)
Driven by **M15** and **M21**.
$$R_{rate} = \frac{Count(R)}{Count(S) + Count(I) + Count(R)}$$
- **Numerator**: Count of Resistant isolates.
- **Denominator**: Total valid tests (S+I+R). Intermediate results dilute the resistance rate (conservative approach).

### 3.2 Antibiotic Pressure (Ecological Metrics)
**Exposure Density ($E_{dens}$)**:
$$E_{dens} = \frac{\text{Total Tests Performed}}{\text{Unique Patient Isolates}}$$

**Shannon Diversity Index ($H$)** (M17 Enforced):
$$H = -\sum_{i \in ValidAbx} p_i \ln p_i$$
where $p_i$ is the proportion of tests for antibiotic $i$.
*Constraint*: Antibiotic $i$ is included in $ValidAbx$ only if its testing coverage in the ward $\ge 20\%$.

### 3.3 Temporal Volatility ($\sigma_{vol}$)
Rolling standard deviation of resistance rate over window $w=4$ weeks:
$$\sigma_{vol} = \text{std}(R_{rate}[t], R_{rate}[t-1], ..., R_{rate}[t-w])$$

## 4. Architecture
- **Input**: Validated Stage 1 Data (`stp_canonical_wide` / `stp_canonical_long`).
- **Engines**: Python modules in `api/analysis_engine/`.
- **Output**:
  - `stp_resistance_rates_weekly` (Operational Dashboards)
  - `stp_stage2_feature_store` (Machine Learning Input - Frozen)

## 5. Verification
Logic verified via `scripts/stp_check_stage2_logic.py`.
- Confirmed strict NA exclusion.
- Confirmed Zero-division handling.
- Confirmed M15 Intermediate handling.
