-- ============================================================
-- MRSA Schema v2 Migration
-- Adds new v2 columns to mrsa_raw_clean training table.
-- Safe to run multiple times (IF NOT EXISTS guards).
-- Run BEFORE mrsa_ingest_stage_a.py re-ingestion.
-- ============================================================

-- 1. Add new feature columns
ALTER TABLE mrsa_raw_clean
    ADD COLUMN IF NOT EXISTS gram_stain VARCHAR(50),
    ADD COLUMN IF NOT EXISTS cell_count_category VARCHAR(10)
        CHECK (cell_count_category IN ('LOW', 'MEDIUM', 'HIGH')),
    ADD COLUMN IF NOT EXISTS recent_antibiotic_use VARCHAR(10) DEFAULT 'Unknown',
    ADD COLUMN IF NOT EXISTS length_of_stay INTEGER DEFAULT 0;

-- 2. Backfill gram_stain from old gram_positivity column
UPDATE mrsa_raw_clean
SET gram_stain = 'GPC'
WHERE gram_positivity = 'GPC'
  AND gram_stain IS NULL;

UPDATE mrsa_raw_clean
SET gram_stain = 'Unknown'
WHERE gram_stain IS NULL;

-- 3. Backfill cell_count_category from old ordinal integer cell_count
--    Old schema: 0–1 = LOW, 2–3 = MEDIUM, 4 = HIGH
UPDATE mrsa_raw_clean
SET cell_count_category = CASE
    WHEN cell_count::integer <= 1 THEN 'LOW'
    WHEN cell_count::integer <= 3 THEN 'MEDIUM'
    ELSE 'HIGH'
END
WHERE cell_count_category IS NULL
  AND cell_count IS NOT NULL
  AND cell_count ~ '^[0-9]+(\.[0-9]+)?$';  -- Match integers AND decimals (e.g. 2.0, 3.5)

-- 4. Default remaining NULLs
UPDATE mrsa_raw_clean
SET cell_count_category = 'LOW'
WHERE cell_count_category IS NULL;

-- ============================================================
-- NOTE: Deprecated columns (age, gender, pus_type, cell_count,
--       gram_positivity) are intentionally LEFT in the table
--       for audit purposes. They are excluded from training
--       queries via the SELECT in ingest/training scripts.
--       Do not DROP them until Stage 6 sign-off.
-- ============================================================
