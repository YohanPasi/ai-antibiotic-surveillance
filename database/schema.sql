-- AST Prediction System Database Schema
-- PostgreSQL 16

-- Table: ast_raw_data
-- Stores the original cleaned dataset from Excel
CREATE TABLE IF NOT EXISTS ast_raw_data (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP,
    date DATE NOT NULL,
    lab_no VARCHAR(100),
    age VARCHAR(20),
    gender VARCHAR(10),
    ward VARCHAR(100),
    bht_no VARCHAR(100),
    sample_type VARCHAR(100),
    pus_type VARCHAR(100),
    cell_count VARCHAR(50),
    gram_positivity VARCHAR(50),
    pure_growth_or_mixed VARCHAR(50),
    growth_time_after VARCHAR(50),
    organism VARCHAR(200),
    sub_organism VARCHAR(200),
    esbl_status VARCHAR(50),
    organism_group VARCHAR(100),
    growth VARCHAR(50),
    -- Store antibiotic results as JSONB for flexibility
    antibiotic_results JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for common queries
CREATE INDEX IF NOT EXISTS idx_ast_raw_date ON ast_raw_data(date);
CREATE INDEX IF NOT EXISTS idx_ast_raw_organism ON ast_raw_data(organism);
CREATE INDEX IF NOT EXISTS idx_ast_raw_ward ON ast_raw_data(ward);

-- Table: ast_weekly_aggregated
-- Pre-computed weekly S% by ward/organism/antibiotic
CREATE TABLE IF NOT EXISTS ast_weekly_aggregated (
    id SERIAL PRIMARY KEY,
    week_start_date DATE NOT NULL,
    ward VARCHAR(100),
    organism VARCHAR(200) NOT NULL,
    antibiotic VARCHAR(200) NOT NULL,
    susceptible_count INTEGER DEFAULT 0,
    intermediate_count INTEGER DEFAULT 0,
    resistant_count INTEGER DEFAULT 0,
    total_tested INTEGER GENERATED ALWAYS AS (susceptible_count + intermediate_count + resistant_count) STORED,
    susceptibility_percent NUMERIC(5, 2) GENERATED ALWAYS AS (
        CASE 
            WHEN (susceptible_count + intermediate_count + resistant_count) > 0 
            THEN (susceptible_count::NUMERIC / (susceptible_count + intermediate_count + resistant_count)::NUMERIC * 100)
            ELSE NULL 
        END
    ) STORED,
    has_sufficient_data BOOLEAN GENERATED ALWAYS AS ((susceptible_count + intermediate_count + resistant_count) >= 10) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(week_start_date, ward, organism, antibiotic)
);

-- Indexes for aggregated data queries
CREATE INDEX IF NOT EXISTS idx_weekly_agg_date ON ast_weekly_aggregated(week_start_date);
CREATE INDEX IF NOT EXISTS idx_weekly_agg_organism ON ast_weekly_aggregated(organism);
CREATE INDEX IF NOT EXISTS idx_weekly_agg_ward ON ast_weekly_aggregated(ward);
CREATE INDEX IF NOT EXISTS idx_weekly_agg_antibiotic ON ast_weekly_aggregated(antibiotic);
CREATE INDEX IF NOT EXISTS idx_weekly_agg_combo ON ast_weekly_aggregated(ward, organism, antibiotic, week_start_date);

-- Table: model_performance
-- Tracks MAE scores and metadata for each trained model
CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    ward VARCHAR(100),
    organism VARCHAR(200) NOT NULL,
    antibiotic VARCHAR(200) NOT NULL,
    model_name VARCHAR(50) NOT NULL,  -- 'SMA', 'Prophet', 'ARIMA'
    mae_score NUMERIC(10, 4),
    training_samples INTEGER,
    validation_samples INTEGER,
    is_best_model BOOLEAN DEFAULT FALSE,
    model_file_path VARCHAR(500),
    trained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hyperparameters JSONB,
    UNIQUE(ward, organism, antibiotic, model_name)
);

-- Index for finding best models
CREATE INDEX IF NOT EXISTS idx_model_perf_best ON model_performance(ward, organism, antibiotic, is_best_model);
CREATE INDEX IF NOT EXISTS idx_model_perf_mae ON model_performance(mae_score);

-- Table: predictions
-- Stores historical predictions and actual outcomes for validation
CREATE TABLE IF NOT EXISTS predictions (
    id SERIAL PRIMARY KEY,
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    target_week_start DATE NOT NULL,
    ward VARCHAR(100),
    organism VARCHAR(200) NOT NULL,
    antibiotic VARCHAR(200) NOT NULL,
    predicted_s_percent NUMERIC(5, 2),
    confidence_interval_lower NUMERIC(5, 2),
    confidence_interval_upper NUMERIC(5, 2),
    model_used VARCHAR(50) NOT NULL,
    mae_score NUMERIC(10, 4),
    alert_level VARCHAR(20),  -- 'Green', 'Amber', 'Red'
    is_ward_level BOOLEAN DEFAULT TRUE,
    actual_s_percent NUMERIC(5, 2),  -- Filled in after the week completes
    prediction_error NUMERIC(10, 4),  -- Calculated after actual data available
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for tracking predictions over time
CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions(target_week_start);
CREATE INDEX IF NOT EXISTS idx_predictions_combo ON predictions(ward, organism, antibiotic);

-- View: best_models
-- Convenience view to get best performing model for each combination
CREATE OR REPLACE VIEW best_models AS
SELECT 
    ward,
    organism,
    antibiotic,
    model_name,
    mae_score,
    training_samples,
    model_file_path,
    trained_at
FROM model_performance
WHERE is_best_model = TRUE
ORDER BY organism, antibiotic, ward;

-- View: organism_level_aggregation
-- Aggregates data across all wards for organism-level predictions
CREATE OR REPLACE VIEW organism_level_aggregation AS
SELECT 
    week_start_date,
    organism,
    antibiotic,
    SUM(susceptible_count) as susceptible_count,
    SUM(intermediate_count) as intermediate_count,
    SUM(resistant_count) as resistant_count,
    SUM(total_tested) as total_tested,
    CASE 
        WHEN SUM(total_tested) > 0 
        THEN (SUM(susceptible_count)::NUMERIC / SUM(total_tested)::NUMERIC * 100)
        ELSE NULL 
    END as susceptibility_percent,
    SUM(total_tested) >= 10 as has_sufficient_data
FROM ast_weekly_aggregated
GROUP BY week_start_date, organism, antibiotic
ORDER BY week_start_date, organism, antibiotic;

COMMENT ON TABLE ast_raw_data IS 'Original AST data from Excel file';
COMMENT ON TABLE ast_weekly_aggregated IS 'Weekly aggregated susceptibility percentages';
COMMENT ON TABLE model_performance IS 'Model training metrics and MAE scores';
COMMENT ON TABLE predictions IS 'Historical predictions for validation tracking';
COMMENT ON VIEW best_models IS 'Best performing model for each ward/organism/antibiotic';
COMMENT ON VIEW organism_level_aggregation IS 'Organism-level aggregation across all wards';
