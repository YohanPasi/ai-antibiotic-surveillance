# MRSA Prediction Feature Set — Canonical Definition

**Version:** 2.0 (Refactor Stage 1)
**Date:** 2026-03-07
**Scope:** Defines the exact inputs the MRSA risk screening model must use. All future models, training scripts, API schemas, and UI forms must follow this document.

---

## 1. Final Approved Feature Set

| # | Feature Name | Type | Values / Range | Clinical Justification |
|---|---|---|---|---|
| 1 | `ward` | Categorical | Hospital-configured master list | Ward-level MRSA prevalence varies significantly; ICU baseline MRSA rate is demonstrably higher than general wards |
| 2 | `sample_type` | Categorical | Hospital-configured master list (Blood, Urine, Wound, Pus, Swab, etc.) | Different specimen types have different MRSA prevalence rates |
| 3 | `gram_stain` | Categorical | `GPC` / `Unknown` | Gram-positive cocci (GPC) is a prerequisite criterion — this is a strong directional indicator |
| 4 | `cell_count_category` | Categorical | `LOW` / `MEDIUM` / `HIGH` | Pus cell count reflects host inflammatory response; higher inflammation correlates with more virulent organisms including MRSA |
| 5 | `growth_time` | Numeric (float, nullable) | Hours ≥ 0, **Blood samples only** | Faster blood culture positivity correlates with higher bacterial load. Excluded for non-blood samples (no equivalent biological meaning) |
| 6 | `recent_antibiotic_use` | Categorical | `Yes` / `No` / `Unknown` | Prior antibiotic exposure selectively pressures resistant organisms — a known MRSA risk factor |
| 7 | `length_of_stay` | Numeric (integer) | Days ≥ 0 | Longer admissions increase MRSA acquisition risk via healthcare exposure |

### 1a. Feature Type Classification for ML Pipeline

This table defines how each feature must be treated during preprocessing. Incorrect encoding is a common source of silent model degradation.

| Feature | ML Type | Preprocessor treatment |
|---|---|---|
| `ward` | Nominal categorical | One-Hot Encoding (OHE) — no ordinal relationship between wards |
| `sample_type` | Nominal categorical | One-Hot Encoding (OHE) — no ordinal relationship between specimen types |
| `gram_stain` | Nominal categorical | One-Hot Encoding (OHE) — binary in practice (GPC / Unknown) |
| `cell_count_category` | **Ordinal categorical** | One-Hot Encoding (OHE) — LOW < MEDIUM < HIGH implies order but OHE is safer for small categories |
| `growth_time` | Numeric continuous | StandardScaler; `-1` sentinel for NULL (non-blood) — do **not** impute with median |
| `recent_antibiotic_use` | Nominal categorical | One-Hot Encoding (OHE) — Yes / No / Unknown are not ordered |
| `length_of_stay` | Numeric integer | StandardScaler — right-skewed distribution expected |

> **Note on `cell_count_category` ordinal encoding:** Although LOW < MEDIUM < HIGH has a natural order, OHE is used instead of label-encoding to avoid implying a precise numeric interval between categories (e.g. the jump from LOW→MEDIUM is not necessarily equal to MEDIUM→HIGH).


---

## 2. Features Removed from Previous Version

The following features were in the old model but are **biologically unjustified** and have been removed from the prediction pipeline.

| Feature | Old Role | Reason for Removal |
|---|---|---|
| `gender` | Categorical predictor | No reproducible clinical evidence that biological sex predicts MRSA acquisition in hospital settings. Adds noise without signal. |
| `pus_type` | Categorical predictor | Inconsistent across labs — classification differs between institutions and reporters, making the feature unreliable. |
| `age` | Numeric predictor | Removed in this pass: age correlates with length-of-stay and comorbidities (both captured implicitly). To be revisited if retraining data shows sufficient discriminative power. |
| `bht` | String field | Administrative hospital identifier. Must **never** enter any ML model — it is a record-keeping field only. |

> **Important:** `gender`, `pus_type`, and `bht` can still appear in the UI for clinical record-keeping, but they must be stripped from the payload before it reaches the prediction model. See Section 6.

---

## 3. Feature Transformations

### 3a. Cell Count → Categorical

Lab microscopy reports pus cells in ranges, not single numbers. The model must accept the categorical label directly:

| Lab report reads | `cell_count_category` value | Biological meaning |
|---|---|---|
| `< 10` cells/hpf | `LOW` | Minimal inflammation |
| `10 – 25` cells/hpf | `MEDIUM` | Moderate inflammation |
| `> 25` cells/hpf | `HIGH` | Severe inflammation — higher MRSA suspicion |

> **Note:** The old system used an ordinal 0–4 integer. This is replaced entirely by LOW/MEDIUM/HIGH. Training data must be re-mapped accordingly (see Stage 4).

### 3b. Growth Time — Blood-Only Rule

```
IF sample_type == "Blood":
    growth_time = <lab-entered value in hours>
ELSE:
    growth_time = NULL
```

The model must treat `NULL` growth_time as a separate signal (not imputed to a median). Implementation detail: use `Optional[float]` in the schema and handle NULL in the preprocessor as a dedicated `growth_time_missing` indicator or simply exclude from non-blood samples at preprocessing time.

---

## 4. UI → Model Feature Mapping

Defines how values entered in the clinical form map to model features. This is the contract between Stage 2 (Frontend) and Stage 3 (Backend).

| UI Label | UI Input Type | Model Feature | Notes |
|---|---|---|---|
| Ward | Dropdown (master data) | `ward` | Direct pass-through |
| Sample type | Dropdown (master data) | `sample_type` | Direct pass-through |
| Gram stain result | Dropdown | `gram_stain` | Options: "Gram-positive cocci (GPC)" → `GPC`, "Not done / Unknown" → `Unknown` |
| Pus cells | Dropdown (not numeric) | `cell_count_category` | Options: `< 10` → `LOW`, `10–25` → `MEDIUM`, `> 25` → `HIGH` |
| Culture growth time (hrs) | Number input (hidden unless Blood) | `growth_time` | Shown only when sample_type = Blood |
| Recent antibiotic use? | Dropdown | `recent_antibiotic_use` | Options: Yes / No / Unknown |
| Length of stay (days) | Number input (integer ≥ 0) | `length_of_stay` | |
| Patient BHT No. | Text input | *(record only — not sent to model)* | Stored in metadata, stripped from prediction payload |

---

## 5. New Conceptual Request Schema (Design — Stage 3 Implementation)

> **Do not implement in code yet.** This is the target schema for Stage 3.

```python
class MRSAPredictionRequest(BaseModel):
    """
    New MRSA Pre-AST Risk Assessment Request (v2.0)
    Reflects clinically validated feature set only.
    """
    ward: str
    sample_type: str
    gram_stain: str   = Field(..., pattern="^(GPC|Unknown)$")
    cell_count_category: str = Field(..., pattern="^(LOW|MEDIUM|HIGH)$")
    growth_time: Optional[float] = Field(None, ge=0)    # Null for non-blood
    recent_antibiotic_use: str = Field(..., pattern="^(Yes|No|Unknown)$")
    length_of_stay: int = Field(..., ge=0)

    # Record-keeping only (not used in prediction)
    bht: Optional[str] = None

    class Config:
        extra = "forbid"
```

**Key changes from v1:**
- Removed: `age`, `gender`, `pus_type`, `cell_count` (integer)
- Added: `cell_count_category` (categorical), `recent_antibiotic_use`, `length_of_stay`
- `gram_positivity` renamed to `gram_stain` for clarity
- `growth_time` changes to `Optional[float]` with explicit `None` default (not 24.0 — blood-only)
- `bht` kept as optional record field but `extra = "forbid"` prevents any other unlisted fields

---

## 6. Data Isolation Rules

These rules are **non-negotiable** and must be enforced at every layer:

| Rule | Where enforced |
|---|---|
| `bht` must never enter the feature vector | Backend preprocessing (strip before model input) |
| `gender`, `pus_type`, `age` must never enter the feature vector | Backend preprocessing + schema exclusion |
| `growth_time` must be NULL for non-Blood samples | Frontend conditional + Backend validator |
| `extra = "forbid"` on all request schemas | Pydantic schema |
| No antibiotic columns anywhere in the feature set | Schema + data ingestion |
| No forecast/future data in the MRSA endpoint | Runtime guard in `mrsa_service.predict()` |

---

## 7. Database Compatibility Check

**Table:** `mrsa_risk_assessments`
**Column:** `input_snapshot JSONB`

**Assessment: ✅ Compatible — No schema change required**

Because `input_snapshot` is a `JSONB` column, it stores the raw request as a flexible JSON object. Adding new fields (`cell_count_category`, `recent_antibiotic_use`, `length_of_stay`) or removing old ones (`gender`, `pus_type`) requires **no database migration**. The new fields will simply be stored in the JSON object when the new schema is submitted.

**Table:** `mrsa_raw_clean` (training store)
**Assessment: ⚠️ Requires column additions in Stage 4**

| Change | Action required |
|---|---|
| Add `cell_count_category` (VARCHAR) | ALTER TABLE or recreate in Stage 4 |
| Add `recent_antibiotic_use` (VARCHAR) | ALTER TABLE or recreate in Stage 4 |
| Add `length_of_stay` (INTEGER) | ALTER TABLE or recreate in Stage 4 |
| Remove `gender`, `pus_type` from training | Drop from SELECT in training query — columns can stay in DB for audit |

**Training data concern:** The current `MRSA_Synthetic_PreAST_Training_12000.xlsx` does not contain `recent_antibiotic_use` or `length_of_stay`. These must either be sourced from real data, synthetically generated, or the feature set must be revised before Stage 4 retraining.

---

## 8. What Changes in Each Stage

| Stage | What changes | This document's role |
|---|---|---|
| Stage 1 (now) | This document | Source of truth for all future stages |
| Stage 2 | Frontend form fields | Reference Section 4 (UI → Model mapping) |
| Stage 3 | Backend schema + preprocessing | Reference Section 5 (new schema) + Section 3 (transformations) |
| Stage 4 | Training data + model retraining | Reference Section 1 (features) + Section 7 (DB changes) |
| Stage 5 | Consensus service + bug fixes | Reference Section 6 (data isolation rules) |
| Stage 6 | Validation + governance | Reference Section 1 (feature set) |

---

## 9. Outstanding Questions for Clinical Review

Before Stage 4 (retraining), the following must be resolved:

1. **`recent_antibiotic_use`** — Is this routinely recorded when a culture is ordered in this system? If not, this feature cannot be used.
2. **`length_of_stay`** — Is admission date stored in the system and accessible at the time of culture ordering?
3. **`age` removal** — Confirm that age should be excluded entirely, or should it stay as a secondary feature with lower weight?
4. **`cell_count < 10 / 10–25 / > 25`** — Confirm these are the exact ranges used in microbiology reports at this hospital, not a generic standard.
