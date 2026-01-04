-- MRSA Stage A: Ingestion & Scope Control
-- Table: mrsa_raw_clean
-- Purpose: Store clean, pre-AST features for supervised learning.
-- Strict Rules: 
-- 1. No antibiotic columns.
-- 2. Staph aureus only.
-- 3. Audit columns separated.

-- Force fresh start
DROP TABLE IF EXISTS mrsa_raw_clean;

CREATE TABLE mrsa_raw_clean (
    id SERIAL PRIMARY KEY,
    
    -- Ground Truth Label (Derived from Sub_Organism)
    mrsa_label INT NOT NULL CHECK (mrsa_label IN (0, 1)), -- 1 = MRSA, 0 = MSSA

    -- Clinical Features (Pre-AST)
    age INT,
    gender VARCHAR(10),
    ward VARCHAR(50), -- Normalized
    sample_type VARCHAR(50), -- Normalized (Blood, Urine, etc.)
    pus_type VARCHAR(50),
    cell_count INT CHECK (cell_count BETWEEN 0 AND 4), -- Ordinal
    gram_positivity VARCHAR(50), -- Normalized (GPC)
    growth_time FLOAT, -- Hours

    -- Audit & Lineage (NOT for Training)
    bht VARCHAR(50),
    original_timestamp TIMESTAMP,
    
    -- Metadata
    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for quick analysis
CREATE INDEX IF NOT EXISTS idx_mrsa_label ON mrsa_raw_clean(mrsa_label);
CREATE INDEX IF NOT EXISTS idx_mrsa_ward ON mrsa_raw_clean(ward);
