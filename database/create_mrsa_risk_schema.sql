CREATE TABLE IF NOT EXISTS mrsa_risk_assessments (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ward VARCHAR(50),
    sample_type VARCHAR(50),
    predicted_probability FLOAT,
    risk_band VARCHAR(10), -- 'GREEN', 'AMBER', 'RED'
    model_version VARCHAR(50),
    clinical_features JSONB -- Store input features for debugging/audit
);

CREATE INDEX IF NOT EXISTS idx_mrsa_risk_timestamp ON mrsa_risk_assessments(timestamp);
CREATE INDEX IF NOT EXISTS idx_mrsa_risk_band ON mrsa_risk_assessments(risk_band);
