-- ESBL Encounters Table (Redesigned for Readability)
-- Stores patient inputs and AI predictions with explicit columns

CREATE TABLE IF NOT EXISTS esbl_encounters (
    -- Primary Key
    encounter_id VARCHAR(50) PRIMARY KEY,
    
    -- Patient Demographics
    age INT,
    gender VARCHAR(10),
    ward VARCHAR(100),
    
    -- Clinical Details
    organism VARCHAR(200) NOT NULL,
    gram_stain VARCHAR(10),  -- GNB, GPC
    sample_type VARCHAR(100),
    cell_count_level VARCHAR(20),
    pus_type VARCHAR(20),
    pure_growth VARCHAR(20),
    
    -- ESBL Risk Prediction
    esbl_probability NUMERIC(5, 4),  -- e.g., 0.6154
    risk_group VARCHAR(20),  -- High, Moderate, Low
    ood_warning BOOLEAN DEFAULT FALSE,
    
    -- Model Metadata
    model_version VARCHAR(50),
    evidence_version VARCHAR(50),
    threshold_version VARCHAR(50),
    
    -- Recommendations (keep as JSONB for array of drugs)
    recommendations JSONB,
    
    -- Status Tracking
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, COMPLETED
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_esbl_enc_organism ON esbl_encounters(organism);
CREATE INDEX IF NOT EXISTS idx_esbl_enc_ward ON esbl_encounters(ward);
CREATE INDEX IF NOT EXISTS idx_esbl_enc_risk ON esbl_encounters(risk_group);
CREATE INDEX IF NOT EXISTS idx_esbl_enc_date ON esbl_encounters(created_at);
