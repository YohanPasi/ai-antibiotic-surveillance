-- STAGE C: BASELINE LEARNING
-- Table to store ward-specific "normal" susceptibility patterns

CREATE TABLE IF NOT EXISTS ast_baselines (
    id SERIAL PRIMARY KEY,
    ward VARCHAR(100) NOT NULL,
    organism VARCHAR(200) NOT NULL,
    antibiotic VARCHAR(200) NOT NULL,
    
    -- Core Baseline Metrics
    baseline_s_percent NUMERIC(5, 2) NOT NULL,  -- Expected "normal" S%
    lower_bound NUMERIC(5, 2) NOT NULL,         -- Early warning threshold
    upper_bound NUMERIC(5, 2),                  -- Optional upper limit
    
    -- Training Metadata
    training_weeks_used INTEGER NOT NULL,       -- How many weeks used to compute baseline
    historical_std_dev NUMERIC(5, 2),           -- Standard deviation of historical S%
    last_trained_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Quality Flag
    sufficient_history BOOLEAN DEFAULT TRUE,    -- TRUE if >= 8-10 weeks available
    
    -- Uniqueness
    UNIQUE(ward, organism, antibiotic)
);

-- Index for fast lookups during surveillance
CREATE INDEX IF NOT EXISTS idx_baselines_combo 
    ON ast_baselines(ward, organism, antibiotic);

COMMENT ON TABLE ast_baselines IS 'Ward-specific baseline S% and tolerance bounds (Stage C)';
COMMENT ON COLUMN ast_baselines.baseline_s_percent IS 'Expected normal S% (SMA/Holt-Winters)';
COMMENT ON COLUMN ast_baselines.lower_bound IS 'Alert threshold (baseline - tolerance)';
