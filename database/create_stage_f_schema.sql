-- STAGE F: Data Entry & Feedback Loop Schema

-- 1. Raw AST Data Entry
-- Stores individual patient AST results entered via the UI.
CREATE TABLE IF NOT EXISTS ast_raw_data (
    id SERIAL PRIMARY KEY,
    lab_no VARCHAR(50),
    age INT,
    gender VARCHAR(10),
    bht VARCHAR(50),
    ward VARCHAR(50) NOT NULL,
    specimen_type VARCHAR(50) NOT NULL,
    organism VARCHAR(100) NOT NULL, -- Non-Fermenters Only
    antibiotic VARCHAR(100) NOT NULL,
    result VARCHAR(5) NOT NULL, -- S / I / R
    entry_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast reporting/aggregation
CREATE INDEX IF NOT EXISTS idx_ast_entry_date ON ast_raw_data(entry_date);
CREATE INDEX IF NOT EXISTS idx_ast_ward_org ON ast_raw_data(ward, organism);
