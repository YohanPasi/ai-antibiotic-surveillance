-- MRSA Stage C: Clinical Risk Logic & API Integration
-- Table: mrsa_risk_assessments
-- Purpose: Audit trail for all MRSA predictions. Stores input snapshot for guaranteed explainability.

DROP TABLE IF EXISTS mrsa_risk_assessments CASCADE;

CREATE TABLE IF NOT EXISTS mrsa_risk_assessments (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Clinical Context
    ward VARCHAR(50),
    sample_type VARCHAR(50),
    
    -- Prediction Result
    mrsa_probability FLOAT,
    risk_band VARCHAR(10), -- GREEN, AMBER, RED
    model_version VARCHAR(50),
    
    -- Critical for Explainability
    input_snapshot JSONB -- Stores the exact input used for this prediction
);

CREATE INDEX IF NOT EXISTS idx_mrsa_risk_timestamp ON mrsa_risk_assessments(timestamp);
