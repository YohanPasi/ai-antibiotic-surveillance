-- ESBL Audit Trail / Governance Logs
-- Stores prediction metadata and stewardship alerts

CREATE TABLE IF NOT EXISTS esbl_audit_logs (
    id SERIAL PRIMARY KEY,
    log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    encounter_id VARCHAR(50),  -- Link to esbl_encounters
    
    -- Patient Context
    ward VARCHAR(100),
    organism VARCHAR(200) NOT NULL,
    age INT,
    
    -- AI Prediction Results
    esbl_probability NUMERIC(5, 2),
    risk_group VARCHAR(20),  -- 'High', 'Low', 'Moderate'
    
    -- Recommendations
    top_recommendation VARCHAR(100),
    recommendation_efficacy NUMERIC(5, 2),
    
    -- Model Metadata
    model_version VARCHAR(50),
    ood_detected BOOLEAN DEFAULT FALSE,
    
    -- Stewardship
    stewardship_domain VARCHAR(100),
    alert_reason TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_esbl_audit_encounter ON esbl_audit_logs(encounter_id);
CREATE INDEX IF NOT EXISTS idx_esbl_audit_date ON esbl_audit_logs(log_date);
