-- MRSA Stage D: Validation Log
-- Stores post-hoc validation of predictions against AST ground truth

CREATE TABLE IF NOT EXISTS mrsa_validation_log (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER REFERENCES mrsa_risk_assessments(id), -- Nullable if no match found, but ideally linked

    ward VARCHAR(50),
    sample_type VARCHAR(50),

    -- Ground Truth from AST
    cefoxitin_result VARCHAR(10), -- 'R', 'S', 'I'
    actual_mrsa BOOLEAN,          -- Derived Truth

    -- Snapshot of Predictions at time T
    rf_band VARCHAR(20),
    lr_band VARCHAR(20),
    xgb_band VARCHAR(20),
    consensus_band VARCHAR(20),
    
    confidence_level VARCHAR(20), -- HIGH, MODERATE, LOW
    model_versions JSONB,         -- Version tracking

    -- Validation Outputs
    rf_correct BOOLEAN,
    lr_correct BOOLEAN,
    xgb_correct BOOLEAN,
    consensus_correct BOOLEAN,

    validation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for analytics
CREATE INDEX IF NOT EXISTS idx_validation_date ON mrsa_validation_log(validation_date);
CREATE INDEX IF NOT EXISTS idx_validation_correct ON mrsa_validation_log(consensus_correct);
