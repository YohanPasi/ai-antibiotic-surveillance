-- STAGE D: CHANGE DETECTION & ALERT ENGINE
-- Audit trail for all surveillance decisions

CREATE TABLE IF NOT EXISTS surveillance_logs (
    id SERIAL PRIMARY KEY,
    log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    week_start_date DATE NOT NULL,
    ward VARCHAR(100),
    organism VARCHAR(200) NOT NULL,
    antibiotic VARCHAR(200) NOT NULL,
    
    -- Metrics
    observed_s_percent NUMERIC(5, 2),
    baseline_s_percent NUMERIC(5, 2),
    
    -- Forecasting (Placeholders for Stage D/E)
    forecast_s_percent NUMERIC(5, 2),
    forecast_deviation NUMERIC(5, 2),
    
    -- Alert Decision
    alert_status VARCHAR(20),  -- 'green', 'amber', 'red'
    alert_reason TEXT,
    
    -- Operational Context
    stewardship_domain VARCHAR(100),
    model_version VARCHAR(50)
);

-- Index for fast retrieval in dashboard
CREATE INDEX IF NOT EXISTS idx_surveillance_logs_week 
    ON surveillance_logs(week_start_date);
    
CREATE INDEX IF NOT EXISTS idx_surveillance_logs_combo 
    ON surveillance_logs(ward, organism, antibiotic);
