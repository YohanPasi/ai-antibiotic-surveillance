-- ============================================================
-- MIGRATION: ESBL → Beta-Lactam Resistance Spectrum Prediction
-- Run this ONCE on the existing database.
-- All ESBL-specific columns are renamed/removed cleanly.
-- ============================================================

BEGIN;

-- ============================================================
-- TABLE 1: esbl_encounters
-- Drop ESBL-specific columns, add beta-lactam spectrum columns
-- ============================================================

-- 1a. Drop ESBL-specific columns
ALTER TABLE esbl_encounters DROP COLUMN IF EXISTS esbl_probability;
ALTER TABLE esbl_encounters DROP COLUMN IF EXISTS risk_group;
ALTER TABLE esbl_encounters DROP COLUMN IF EXISTS threshold_version;
ALTER TABLE esbl_encounters DROP COLUMN IF EXISTS ood_warning;

-- 1b. Add new beta-lactam spectrum prediction columns
ALTER TABLE esbl_encounters ADD COLUMN IF NOT EXISTS
    predicted_beta_lactam_spectrum JSONB;
    -- JSONB shape:
    -- {
    --   "Gen1": { "probability": 0.82, "traffic_light": "Green" },
    --   "Gen2": { "probability": 0.61, "traffic_light": "Amber" },
    --   "Gen3": { "probability": 0.18, "traffic_light": "Red"   },
    --   "Gen4": { "probability": 0.71, "traffic_light": "Green" },
    --   "Carbapenem": { "probability": 0.93, "traffic_light": "Green" }
    -- }

ALTER TABLE esbl_encounters ADD COLUMN IF NOT EXISTS
    top_generation_recommendation VARCHAR(50);
    -- e.g. "Gen1", "Gen2", "Carbapenem"

ALTER TABLE esbl_encounters ADD COLUMN IF NOT EXISTS
    predicted_success_probability NUMERIC(5, 4);
    -- Probability that top_generation_recommendation will succeed

ALTER TABLE esbl_encounters ADD COLUMN IF NOT EXISTS
    spectrum_ood_warning BOOLEAN DEFAULT FALSE;
    -- OOD flag for day-0 inputs vs new model's training distribution

ALTER TABLE esbl_encounters ADD COLUMN IF NOT EXISTS
    top_feature_influences JSONB;
    -- SHAP top-3 contributing features for audit/explainability
    -- e.g. [{"feature": "Ward_ICU", "shap_value": 0.32}, ...]

-- 1c. Update model_version and evidence_version to generic naming
--     (no data change needed — values will just be different strings going forward)
COMMENT ON COLUMN esbl_encounters.model_version IS
    'Model artifact version, e.g. beta_lactam_xgb_v1';
COMMENT ON COLUMN esbl_encounters.evidence_version IS
    'Evidence/outcome table version used for recommendation scoring';

-- ============================================================
-- TABLE 2: esbl_lab_results
-- Add a generation column to map each antibiotic to its class
-- ============================================================

ALTER TABLE esbl_lab_results ADD COLUMN IF NOT EXISTS
    generation VARCHAR(20);
    -- Standard beta-lactam generation mapping:
    --   Gen1      → Cefalexin, Cefazolin
    --   Gen2      → Cefuroxime (CXM), Cefaclor
    --   Gen3      → Ceftriaxone (CRO), Cefotaxime (CTX), Ceftazidime (CAZ)
    --   Gen4      → Cefepime
    --   Carbapenem→ Meropenem (MEM), Imipenem (IMP), Ertapenem (ETP)
    --   BL_Combo  → Pip-Tazo (TZP), Amoxiclav (AMC)
    --   Non_BL    → Aminoglycosides, Fluoroquinolones, etc.

-- Populate generation for existing rows based on antibiotic name
UPDATE esbl_lab_results SET generation = CASE
    WHEN antibiotic ILIKE '%cefalexin%'   OR antibiotic ILIKE '%cefazolin%'                         THEN 'Gen1'
    WHEN antibiotic ILIKE '%cefuroxime%'  OR antibiotic ILIKE '%cxm%'   OR antibiotic ILIKE '%cefaclor%'  THEN 'Gen2'
    WHEN antibiotic ILIKE '%ceftriaxone%' OR antibiotic ILIKE '%cro%'
      OR antibiotic ILIKE '%cefotaxime%'  OR antibiotic ILIKE '%ctx%'
      OR antibiotic ILIKE '%ceftazidime%' OR antibiotic ILIKE '%caz%'                               THEN 'Gen3'
    WHEN antibiotic ILIKE '%cefepime%'    OR antibiotic ILIKE '%fep%'                               THEN 'Gen4'
    WHEN antibiotic ILIKE '%meropenem%'   OR antibiotic ILIKE '%mem%'
      OR antibiotic ILIKE '%imipenem%'    OR antibiotic ILIKE '%imp%'
      OR antibiotic ILIKE '%ertapenem%'   OR antibiotic ILIKE '%etp%'                               THEN 'Carbapenem'
    WHEN antibiotic ILIKE '%pip%'         OR antibiotic ILIKE '%tazo%'   OR antibiotic ILIKE '%tzp%'
      OR antibiotic ILIKE '%amoxiclav%'   OR antibiotic ILIKE '%amc%'   OR antibiotic ILIKE '%augment%' THEN 'BL_Combo'
    ELSE 'Non_BL'
END
WHERE generation IS NULL;

-- Make generation NOT NULL going forward (after backfill)
ALTER TABLE esbl_lab_results ALTER COLUMN generation SET DEFAULT 'Non_BL';

-- ============================================================
-- TABLE 3: esbl_audit_logs
-- Replace ESBL-specific columns with spectrum prediction columns
-- ============================================================

-- 3a. Drop ESBL-specific audit columns
ALTER TABLE esbl_audit_logs DROP COLUMN IF EXISTS esbl_probability;
ALTER TABLE esbl_audit_logs DROP COLUMN IF EXISTS top_recommendation;
ALTER TABLE esbl_audit_logs DROP COLUMN IF EXISTS recommendation_efficacy;
ALTER TABLE esbl_audit_logs DROP COLUMN IF EXISTS stewardship_domain;

-- 3b. Add beta-lactam spectrum audit columns
ALTER TABLE esbl_audit_logs ADD COLUMN IF NOT EXISTS
    predicted_beta_lactam_spectrum JSONB;
    -- Full spectrum prediction stored for traceability

ALTER TABLE esbl_audit_logs ADD COLUMN IF NOT EXISTS
    top_generation_recommendation VARCHAR(50);
    -- e.g., "Gen1", "Carbapenem"

ALTER TABLE esbl_audit_logs ADD COLUMN IF NOT EXISTS
    traffic_light_summary VARCHAR(10);
    -- Highest-risk traffic light across all generations: Green / Amber / Red

ALTER TABLE esbl_audit_logs ADD COLUMN IF NOT EXISTS
    predicted_success_probability NUMERIC(5, 2);
    -- Success probability for top recommended generation

ALTER TABLE esbl_audit_logs ADD COLUMN IF NOT EXISTS
    top_feature_influences JSONB;
    -- SHAP top-3 features used in prediction

ALTER TABLE esbl_audit_logs ADD COLUMN IF NOT EXISTS
    ood_detected BOOLEAN DEFAULT FALSE;
    -- Renamed from old ood_detected (if it already exists, this is a no-op)

ALTER TABLE esbl_audit_logs ADD COLUMN IF NOT EXISTS
    clinician_override VARCHAR(10);
    -- 'ACCEPT' or 'OVERRIDE' — set by post-prediction decision

ALTER TABLE esbl_audit_logs ADD COLUMN IF NOT EXISTS
    override_reason TEXT;
    -- Free-text reason code for override decisions

-- 3c. Rename alert_reason to a more neutral name
ALTER TABLE esbl_audit_logs RENAME COLUMN alert_reason TO governance_note;

COMMIT;
