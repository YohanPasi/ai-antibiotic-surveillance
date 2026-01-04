-- Add columns to mrsa_risk_assessments for multi-model storage
-- This enables auditing of Consensus Logic and individual model decisions

ALTER TABLE mrsa_risk_assessments
ADD COLUMN IF NOT EXISTS rf_probability FLOAT,
ADD COLUMN IF NOT EXISTS rf_risk_band VARCHAR(50),
ADD COLUMN IF NOT EXISTS rf_version VARCHAR(50),

ADD COLUMN IF NOT EXISTS lr_probability FLOAT,
ADD COLUMN IF NOT EXISTS lr_risk_band VARCHAR(50),
ADD COLUMN IF NOT EXISTS lr_version VARCHAR(50),

ADD COLUMN IF NOT EXISTS xgb_probability FLOAT,
ADD COLUMN IF NOT EXISTS xgb_risk_band VARCHAR(50),
ADD COLUMN IF NOT EXISTS xgb_version VARCHAR(50),

ADD COLUMN IF NOT EXISTS consensus_band VARCHAR(50),
ADD COLUMN IF NOT EXISTS confidence_level VARCHAR(50), -- HIGH, MODERATE, LOW
ADD COLUMN IF NOT EXISTS consensus_version VARCHAR(50); -- e.g. 'C5_v1'

-- Index for querying by confidence (useful for finding disagreements)
CREATE INDEX IF NOT EXISTS idx_risk_confidence ON mrsa_risk_assessments(confidence_level);
