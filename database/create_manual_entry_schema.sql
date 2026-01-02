-- STAGE F: Manual AST Data Entry Schema

-- 1. Manual AST Entry Table
-- Stores individual patient AST results entered manual via the UI.
CREATE TABLE IF NOT EXISTS ast_manual_entry (
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
CREATE INDEX IF NOT EXISTS idx_manual_entry_date ON ast_manual_entry(entry_date);
CREATE INDEX IF NOT EXISTS idx_manual_ward_org ON ast_manual_entry(ward, organism);
