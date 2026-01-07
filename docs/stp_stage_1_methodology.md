# Streptococcus & Enterococcus Surveillance: Stage 1 Methodology
===========================================================

**Dataset Version**: v1.0.0
**Governance Level**: Research-Grade (M1-M10 Compliance)
**Status**: Stage 1 Complete (Foundation Layer)

---

## 1. Overview and Scope

This document outlines the methodological framework for the **Stage 1 STP Surveillance System**, establishing a validated, reproducible data foundation for analyzing antibiotic resistance patterns in *Streptococcus pneumoniae*, *Streptococcus agalactiae*, *Viridans group streptococci*, *Enterococcus faecalis*, and *Enterococcus faecium*.

**Primary Objective**: To ingest, validate, and structure retrospective laboratory data into a canonical format suitable for subsequent modeling (Stage 2+) without introducing bias or clinical errors.

### 1.1 Inclusion Criteria
*   **Organisms**:
    *   *Streptococcus pneumoniae*
    *   *Streptococcus agalactiae* (Group B Strep)
    *   *Viridans streptococci*
    *   *Enterococcus faecalis*
    *   *Enterococcus faecium*
*   **Data Source**: Laboratory Information System (LIS) extracts (Excel format).
*   **Time Period**: 2023–2025 (Retrospective).

### 1.2 Exclusion Criteria
*   Any organism not listed in the inclusion criteria (automatically rejected).
*   Records with missing sample dates.
*   Records with missing laboratory identifiers (isolate IDs).

---

## 2. Data Governance & Integrity (M1-M10 Framework)

This system implements the **M1-M10 Governance Framework** to ensure scientific rigor and publication readiness.

### M1: Isolate Episode Governance
*   **Policy**: All laboratory isolates are retained as independent observations.
*   **Implementation**: No episode-level deduplication (e.g., collapsing repeat isolates from the same patient) is performed at Stage 1. This preserves raw laboratory reporting fidelity.
*   **Justification**: Allows for downstream sensitivity analyses (e.g., comparing "all isolates" vs. "first isolate per patient") during statistical modeling stages (Stage 4).

### M2: AST Panel Heterogeneity
*   **Policy**: Differences in antibiotic testing panels across organisms and wards are preserved as recorded.
*   **Implementation**: Missing antibiotic results are encoded as `NA` ("Not Tested") and are distinguished from resistance outcomes. No imputation is performed.
*   **Justification**: Accurately reflects real-world laboratory workflows and prevents artificial inflation/deflation of resistance rates.

### M3: Temporal Density Validation
*   **Policy**: Temporal data density is assessed to identify sparse sampling periods.
*   **Implementation**: Monthly isolate counts are monitored. Periods with <20 isolates are flagged in the dataset metadata but are not removed.
*   **Justification**: Ensures transparency regarding data availability for time-series analysis.

### M4: Negative Control Declaration
*   **Policy**: Stage 1 strictly excludes outcome variables, clinical endpoints, or proxy labels involved in later prediction tasks.
*   **Implementation**: Derived fields are limited to metadata normalization (e.g., standardizing ward names).
*   **Justification**: Prevents data leakage and implicit supervision ("cheating") in future predictive models.

### M5: Database Migration Version Safety
*   **Policy**: All schema changes and dataset versions are cryptographically tracked.
*   **Implementation**: SHA-256 hashes of the source data file and the database schema are stored in the `stp_dataset_metadata` table.
*   **Justification**: Guarantees reproducibility and auditability of the data environment.

### M6: Freeze Logic
*   **Policy**: Validated datasets are immutable.
*   **Implementation**: The ingestion pipeline enforces a "Freeze" status. Re-ingesting an existing version requires an explicit `force_reload` flag or a version increment.

---

## 3. Data Processing Pipeline

The Stage 1 pipeline consists of six sequential steps, orchestrated by `stp_run_stage_1_pipeline.py`.

### 3.1 Ingestion & Validation (`stp_stage_1_ingest.py`)
*   **Input**: Raw Excel File.
*   **Hash Check**: Computes SHA-256 of input file.
*   **Normalization**: Maps organism names to canonical taxonomy (e.g., "Strep. pneumoniae" → "Streptococcus pneumoniae").
*   **Validation**: Rejects rows failing inclusion criteria. 
*   **Output**: `stp_raw_wide` table (Supabase).

### 3.2 Transformation (`stp_wide_to_long_transform.py`)
*   **Process**: Unpivots wide-format AST data (one column per antibiotic) into long-format (one row per test).
*   **Performance**: Uses optimized batch insertion (`psycopg2.extras.execute_values`).
*   **Output**: `stp_canonical_long` table (Supabase).

### 3.3 Antibiotic Registry (`stp_build_antibiotic_registry.py`)
*   **Process**: Scans the dataset to dynamically generate the list of tested antibiotics.
*   **Output**: `stp_antibiotic_registry` table (Supabase).
*   **Note**: Determines the "Menu" of antibiotics available for analysis based on actual data, not theoretical lists.

### 3.4 Governance Reporting (`stp_generate_governance_report.py`)
*   **Process**: Generates M1-M10 and O1-O2 declarations and stores them in the database.
*   **Output**: `stp_governance_declarations` table (Supabase).

### 3.5 Descriptive Statistics (`stp_descriptive_stats.py`)
*   **Process**: Computes sample sizes, temporal distributions, and testing frequencies.
*   **Constraint**: strictly strictly **forbidden** from calculating resistance rates or trends (Stage 2 firewall).
*   **Output**: JSON statistics in `stp_dataset_metadata` or separate stats storage.

### 3.6 Column Provenance (`stp_populate_column_provenance.py`)
*   **Process**: Maps every database column to its origin (Source File vs. Derived).
*   **Output**: `stp_column_provenance` table (Supabase).

---

## 4. Operational Awareness (O1-O2)

### O1: CLSI/EUCAST Alignment
*   **Disclaimer**: Breakpoint interpretations (S/I/R) are adopted directly from the LIS. Stage 1 does not re-interpret raw MIC values (which are unavailable).

### O2: Ward Function Drift
*   **Disclaimer**: Ward designations (`ICU`, `Ward 12`, etc.) reflect the hospital structure at the time of sampling.

---

## 5. API Integration

Stage 1 exposes the following endpoints via FastAPI for research access:

*   `POST /api/stp/stage1/ingest`: Trigger the full pipeline.
*   `GET /api/stp/stage1/metadata`: Retrieval of versioning and provenance info.
*   `GET /api/stp/stage1/governance`: Access to M1-M10 declarations.
*   `GET /api/stp/stage1/quality-log`: Review of rejected rows and reasons.
*   `GET /api/stp/stage1/descriptive-stats`: Summary statistics (counts only).
*   `GET /api/stp/stage1/canonical-data`: Export of validated long-format data.

---

## 6. Conclusion

The **STP Stage 1** implementation provides a robust, governable foundation for antibiotic surveillance. By decoupling data validation from analysis and enforcing strict strict governance protocols, it ensures that all subsequent insights—whether simple resistance rates (Stage 2) or complex predictive models (Stage 5)—are built upon ground truth.
