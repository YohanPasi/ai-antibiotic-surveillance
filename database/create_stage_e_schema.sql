-- STAGE E: Continuous Learning & Governance Schema

-- 1. Forecast Validation Log
-- Tracks the accuracy of AI predictions against subsequent real-world data.
-- "Did the AI predict the drop in Meropenem sensitivity correctly?"
CREATE TABLE IF NOT EXISTS forecast_validation_log (
    id SERIAL PRIMARY KEY,
    ward VARCHAR(50),
    organism VARCHAR(100),
    antibiotic VARCHAR(100),
    forecast_week DATE,          -- The future date that was predicted
    predicted_s_percent FLOAT,   -- The value the AI predicted
    actual_s_percent FLOAT,      -- The real value observed when the date arrived
    error FLOAT,                 -- actual - predicted
    direction_correct BOOLEAN,   -- Did both go up/down together?
    model_version VARCHAR(50),   -- Traceability: Which model made this guess?
    validation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. LSTM Forecasts (The "Future" Truth)
-- Stores the official predictions for upcoming weeks.
-- Separates "Speculation" from "Surveillance Logs".
CREATE TABLE IF NOT EXISTS lstm_forecasts (
    id SERIAL PRIMARY KEY,
    ward VARCHAR(50),
    organism VARCHAR(100),
    antibiotic VARCHAR(100),
    forecast_week DATE,          -- Target week (T+1)
    predicted_s_percent FLOAT,
    model_version VARCHAR(50),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 3. Model Registry (The "Brain" History)
-- Tracks the lifecycle of the LSTM models.
-- "When was the last time we retrained? Was it better?"
CREATE TABLE IF NOT EXISTS model_registry (
    id SERIAL PRIMARY KEY,
    model_version VARCHAR(50) UNIQUE,
    trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    training_data_start DATE,
    training_data_end DATE,
    epochs INT,
    final_loss FLOAT,
    training_duration_seconds FLOAT,
    is_active BOOLEAN DEFAULT TRUE -- Current production model
);

-- Index for fast retrieval during validation
CREATE INDEX IF NOT EXISTS idx_forecast_validation_week ON forecast_validation_log(forecast_week);
CREATE INDEX IF NOT EXISTS idx_lstm_forecasts_week ON lstm_forecasts(forecast_week);
