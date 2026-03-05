-- Phase 3A Migration v2 — corrected for actual production schema
-- predictions table already exists with actual_s_percent and prediction_error columns
-- We need to:
--   1. Add revision_flag + direction_correct to predictions
--   2. Create forecast_validation_log as a proper audit log (was empty/nonexistent)
--   3. Add indexes

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Extend predictions table with Phase 3A audit columns
-- ─────────────────────────────────────────────────────────────────────────────
ALTER TABLE predictions
  ADD COLUMN IF NOT EXISTS direction_correct BOOLEAN,      -- NULL when no prior week
  ADD COLUMN IF NOT EXISTS revision_flag     BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS validated_at      TIMESTAMP;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Create forecast_validation_log as full audit trail
--    Separate from predictions — keeps a revision history entry per change.
-- ─────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS forecast_validation_log (
    id                  SERIAL PRIMARY KEY,
    ward                VARCHAR(100) NOT NULL,
    organism            VARCHAR(200) NOT NULL,
    antibiotic          VARCHAR(200) NOT NULL,
    forecast_week       DATE         NOT NULL,
    predicted_s_percent FLOAT        NOT NULL,
    actual_s_percent    FLOAT        NOT NULL,
    prediction_error    FLOAT        NOT NULL,
    direction_correct   BOOLEAN,                           -- NULL when no prior week
    revision_flag       BOOLEAN      DEFAULT FALSE,
    validated_at        TIMESTAMP    DEFAULT NOW(),
    model_version       VARCHAR(100)
);

-- One row per (ward, org, abx, week) — prevents double validation
-- ON CONFLICT used for upserts; revision rows use a different INSERT
CREATE UNIQUE INDEX IF NOT EXISTS idx_fvl_unique
  ON forecast_validation_log (ward, organism, antibiotic, forecast_week);

-- Speed up target-level rolling MAE queries (Phase 3B)
CREATE INDEX IF NOT EXISTS idx_fvl_target
  ON forecast_validation_log (ward, organism, antibiotic);

-- Speed up rolling window queries (G1 + G6)
CREATE INDEX IF NOT EXISTS idx_fvl_week
  ON forecast_validation_log (forecast_week);

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Verify
-- ─────────────────────────────────────────────────────────────────────────────
-- SELECT column_name FROM information_schema.columns
-- WHERE table_name IN ('predictions', 'forecast_validation_log')
-- ORDER BY table_name, ordinal_position;
