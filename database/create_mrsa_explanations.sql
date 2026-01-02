CREATE TABLE IF NOT EXISTS mrsa_explanations (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER REFERENCES mrsa_risk_assessments(id), -- Link to prediction
    feature VARCHAR(100),
    contribution FLOAT,
    direction VARCHAR(10), -- 'increase' or 'decrease'
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mrsa_explanations_assessment ON mrsa_explanations(assessment_id);
