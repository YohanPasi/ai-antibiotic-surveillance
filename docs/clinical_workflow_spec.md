
# Clinical Workflow Specification: AI-Antibiotic Surveillance System

## ⚠️ Responsibility Statement
**Final treatment decisions remain the responsibility of the treating clinician.**
This system provides decision support only and does not prescribe or enforce therapy.

---

## 🔵 Phase 1: Pre-AST (Empiric Phase)

**Objective:** Provide risk-based guidance while antibiotic susceptibility results are pending.

### 1.1 Trigger
*   Culture sample registered.
*   Organism identification matches inclusion criteria (**Enterobacterales**).
*   AST results **Pending/Unavailable**.

### 1.2 Clinical Inputs
*   **Patient Demographics:** Age, Gender.
*   **Sample Context:** Ward/Unit, Sample Type.
*   **Microbiology:** Gram Stain (GNB), Organism ID (if available).
*   **Clinical Vitals (Optional):** Length of stay (Growth time as proxy).

### 1.3 System Actions
1.  **Scope Check:** Verify organism is `Enterobacterales` and Gram is `GNB`.
2.  **Risk Prediction (Stage 5):** Calculate probability of ESBL phenotype.
3.  **Risk Stratification (Stage 6):** Assign Low / Moderate / High risk category.
4.  **Recommendation (Stage 7):** Generate ranked list of antibiotics based on:
    *   Expected Bayesian Success.
    *   Stewardship Constraints.
    *   Local antibiogram evidence.

### 1.4 System Outputs (Clinician View)
*   **ESBL Probability:** Numeric (e.g., "82%").
*   **Risk Group:** Visual Indicator (e.g., 🔴 High Risk).
*   **Recommendations:** Top 3-5 antibiotics sorted by Score.
    *   *Display:* Drug Name, Confidence Level, Stewardship Note.
*   **Mandatory Warnings (Non-dismissable):**
    *   "Empiric decision support only."
    *   "Do not delay AST-guided therapy."
    *   "Low Risk does not equal Zero Risk."

### 1.5 Clinician Actions
*   **Accept:** Select a recommended agent -> Log selection.
*   **Override:** Select non-recommended agent -> **Mandatory:** Select reason code (e.g., "Allergy", "Clinical Instability").
*   **Reject:** Ignore system advice.

---

## 🔒 Phase 2: Decision Freeze

**Objective:** Prevent misuse of probabilistic models once definitive data exists.

### 2.1 Trigger
*   AST results uploaded to LIMS/Database.

### 2.2 System Actions
1.  **Lock Prediction:** Empiric ESBL score is frozen/hidden.
2.  **Disable Recommendation Engine:** Probabilistic ranking logic is deactivated for this patient case.
3.  **Visual Lock:** System displays banner:
    > "AST Results Available – Empiric Prediction Disabled."

---

## 🟢 Phase 3: Post-AST (Confirmatory Phase)

**Objective:** Transition to definitive, narrow-spectrum therapy.

### 3.1 Inputs
*   Confirmed AST results (S / I / R) for panel antibiotics.
*   Current active antibiotic (from Phase 1).

### 3.2 System Actions
1.  **Check Empiric Choice:**
    *   Matches AST Susceptibility? -> "Appropriate"
    *   Matches Resistance? -> "escalation REQUIRED"
    *   Matches Susceptible but Broad Spectrum? -> "De-escalation Recommended"
2.  **De-escalation Logic:**
    *   If on Carbapenem & Sensitive to Pip-Tazo/Cefepime -> Flag for Step-down.
    *   If on Combo & Sensitive to Monotherapy -> Flag for Step-down.

### 3.3 System Outputs
*   **AST Table:** Standard S/I/R grid.
*   **Stewardship Message:** 
    *   "Organism is ESBL Negative. Please de-escalate to non-carbapenem."
    *   "Empiric choice was Resistant. Change therapy immediately."

---

## 📝 Audit & Feedback Loop (Backend)

*   All Phase 1 predictions and Phase 3 outcomes are logged.
*   **No Online Learning:** System does **not** update weights based on individual cases.
*   **Traceability:** Every recommendation is linked to Model Version + Data Version.
