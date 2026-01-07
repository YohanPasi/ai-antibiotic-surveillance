# STP Stage Boundary Contract

**M10: Architectural Discipline Between Stages**

---

## Purpose

This document defines the strict boundaries between Stage 1 (Data Foundation) and Stage 2+ (Analytics & Modeling) to prevent:
- Data leakage
- Architectural contamination
- Implicit supervision
- Temporal integrity violations

---

## Stage 1: Data Foundation & Governance Layer

### Responsibilities
✅ **ALLOWED**:
- Load and validate raw data
- Normalize organism/ward names
- Standardize AST values (S/I/R/NA)
- Transform wide→long format
- Generate descriptive statistics (counts, distributions)
- Document data quality (audit trail)
- Compute temporal density (M3)
- Track antibiotic coverage
- Generate governance documentation

❌ **FORBIDDEN**:
- Compute resistance rates
- Compute susceptibility percentages
- Perform trend analysis
- Compute correlations
- Statistical hypothesis testing
- Predictive modeling
- Risk scoring
- Feature engineering (beyond normalization)
- Import modeling libraries (sklearn, statsmodels, prophet, tensorflow, pytorch)

### Outputs (Read-Only for Stage 2+)
- `stp_canonical_long` table (via `stp_stage1_readonly` view)
- `stp_dataset_metadata`
- `stp_governance_declarations`
- `stp_antibiotic_registry`

---

## Stage 2+: Analytics & Modeling Layers

### Responsibilities
✅ **ALLOWED**:
- Read from `stp_stage1_readonly` view ONLY
- Compute resistance rates
- Perform temporal trend analysis
- Build predictive models
- Generate alerts
- Feature engineering
- Statistical testing (with appropriate controls)

❌ **FORBIDDEN**:
- Write to Stage 1 tables
- Access raw Excel files directly
- Modify organism/ward taxonomies
- Bypass Stage 1 validation
- Read from `stp_raw_wide` or `stp_canonical_long` directly (use view instead)

### Inputs (Read-Only)
- `stp_stage1_readonly` view (frozen datasets only)
- `stp_metadata` (for versions, date ranges)
- `stp_antibiotic_registry` (for panel composition)

---

## Enforcement Mechanisms

### 1. Database-Level
```sql
-- Stage 1 tables: Service role write access only
-- Stage 2 read-only view
CREATE VIEW stp_stage1_readonly AS
SELECT * FROM stp_canonical_long
WHERE dataset_version IN (
    SELECT dataset_version 
    FROM stp_dataset_metadata 
    WHERE is_frozen = TRUE
);
```

### 2. Code-Level
```python
# In Stage 1 modules
"""
M10 STAGE BOUNDARY: This module is Stage 1 only.
Forbidden operations: resistance rates, trends, modeling
"""

FORBIDDEN_IMPORTS = ['sklearn', 'statsmodels', 'prophet', 'tensorflow', 'torch']
```

### 3. Test-Level
```python
def test_no_resistance_rates_in_stage1():
    """M10: Verify Stage 1 does not compute resistance rates."""
    forbidden = ['resistant_count / total_tested', 'S_count / total']
    for file in STAGE1_FILES:
        content = read_file(file)
        for pattern in forbidden:
            assert pattern not in content
```

---

## Temporal Integrity Rules (M10)

### Critical Rule
**At time `t`, only data where `sample_date ≤ t` is visible.**

### Enforcement
```python
def assert_no_future_leakage(data, reference_date):
    """
    M10: Validate no future data is present.
    Raises ValueError if future dates detected.
    """
    future_rows = data[data['sample_date'] > reference_date]
    if len(future_rows) > 0:
        raise ValueError(f"DATA LEAKAGE: {len(future_rows)} future rows")
```

### Time-Series Split
```python
# Stage 2+ training/testing must respect temporal order
train, test = get_temporal_split(
    data=canonical_data,
    cutoff_date=split_date
)

# Verify no leakage
assert_no_future_leakage(train, cutoff_date)
```

---

## File Organization

### Stage 1 Files
```
api/data_processor/
├── stp_stage_1_ingest.py          # Validation & ingestion
├── stp_wide_to_long_transform.py  # Format transformation
├── stp_build_antibiotic_registry.py
├── stp_generate_governance_report.py
├── stp_descriptive_stats.py       # Counts only
└── stp_populate_column_provenance.py

api/utils/
├── stp_dataset_hasher.py          # M5 integrity
└── stp_time_utils.py              # M10 temporal enforcement
```

### Stage 2+ Files (Future)
```
api/analytics/
├── stp_stage_2_resistance_rates.py
├── stp_stage_3_trend_analysis.py
└── stp_stage_4_predictive_models.py
```

---

## Violation Detection

### Automated Checks
1. **Import Analysis**: ast.parse() to detect forbidden libraries
2. **Pattern Matching**: Regex for resistance rate computations
3. **Database Audit**: Log all table access
4. **Test Suite**: `test_stp_stage_boundary.py`

### Manual Review
- Code review checklist includes Stage Boundary compliance
- Pull requests must not mix Stage 1 and Stage 2 code

---

## Stage 2 Example (Compliant)

```python
# ✅ CORRECT: Stage 2 reads from read-only view
from sqlalchemy import text

def compute_resistance_rates(organism, antibiotic):
    """
    Stage 2: Compute resistance rates.
    M10 Compliant: Uses read-only view, stage boundary respected.
    """
    query = text("""
        SELECT 
            sample_date,
            COUNT(CASE WHEN ast_result = 'R' THEN 1 END) as resistant,
            COUNT(CASE WHEN ast_result IN ('S', 'I', 'R') THEN 1 END) as total
        FROM stp_stage1_readonly  -- ✅ Read-only view
        WHERE organism = :org AND antibiotic = :abx
        GROUP BY sample_date
    """)
    
    result = db.execute(query, {'org': organism, 'abx': antibiotic})
    # ... compute rates
```

### Stage 2 Example (VIOLATION)

```python
# ❌ WRONG: Direct access to Stage 1 table
def compute_resistance_rates_WRONG(organism, antibiotic):
    """
    ❌ M10 VIOLATION: Bypasses read-only view
    """
    query = text("""
        SELECT * FROM stp_canonical_long  -- ❌ Direct access forbidden
        WHERE organism = :org
    """)
```

---

## Benefits of Strict Boundaries

1. **Prevents Data Leakage**: Temporal integrity enforced
2. **Architectural Clarity**: Each stage has defined scope
3. **Reproducibility**: Changes isolated to specific stages
4. **Code Review**: Easy to verify compliance
5. **Publication Defense**: Clear methodology separation

---

## Consequences of Violations

### Publication Risk
- "Did you use future data to train your model?" → REJECT
- "How do you prevent data leakage?" → UNCLEAR METHODOLOGY

### Technical Debt
- Mixed concerns make refactoring difficult
- Unclear ownership of validation logic
- Testing becomes complex

---

## Approval Process

### Stage 1 → Stage 2 Gatekeeper
Before Stage 2 can begin:
1. Stage 1 dataset must be **frozen** (M6)
2. Governance report must be **approved**
3. Reproducibility must be **verified**
4. All tests must **pass**
5. Stage boundary tests must **pass**

### Sign-Off Required
- Lead researcher
- Ethics committee (if applicable)
- Technical reviewer

---

## Maintenance

### When Adding New Stages
1. Update this contract
2. Add new rows to boundary test suite
3. Update database views
4. Document new boundaries

### When Modifying Stages
1. Verify no boundary crossings
2. Run full test suite
3. Update affected documentation

---

## References

- **M10**: Stage Boundary Enforcement (governance component)
- **M3**: Temporal Density Validation (enables future analyses)
- **M4**: Negative Control Declaration (prevents implicit supervision)
- **M6**: Dataset Freeze (ensures Stage 1 stability)

---

*This contract is part of the M1-M10 governance framework and is enforced via automated testing (test_stp_stage_boundary.py).*

**Version**: 1.0.0  
**Last Updated**: 2026-01-07  
**Status**: ACTIVE
