CREATE TABLE IF NOT EXISTS mrsa_validation_log (
    id SERIAL PRIMARY KEY,
    prediction_id INTEGER, -- Link to mrsa_risk_assessments.id
    ward VARCHAR(50),
    predicted_probability FLOAT,
    predicted_risk_band VARCHAR(10),
    actual_mrsa BOOLEAN,
    prediction_correct BOOLEAN,
    validation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model_version VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_mrsa_validation_actual ON mrsa_validation_log(actual_mrsa);
CREATE INDEX IF NOT EXISTS idx_mrsa_validation_correct ON mrsa_validation_log(prediction_correct);
