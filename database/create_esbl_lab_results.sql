-- ESBL Lab Results / Confirmed AST Data
-- Stores final verified susceptibility results

CREATE TABLE IF NOT EXISTS esbl_lab_results (
    id SERIAL PRIMARY KEY,
    encounter_id VARCHAR(50) NOT NULL,  -- Link to esbl_encounters
    
    -- Patient Details
    lab_no VARCHAR(50),
    age INT,
    gender VARCHAR(10),
    bht VARCHAR(50),
    ward VARCHAR(50) NOT NULL,
    specimen_type VARCHAR(50) NOT NULL,
    organism VARCHAR(100) NOT NULL,
    
    -- AST Result
    antibiotic VARCHAR(100) NOT NULL,
    result VARCHAR(5) NOT NULL,  -- S / I / R
    
    -- Timestamps
    entry_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_esbl_lab_encounter ON esbl_lab_results(encounter_id);
CREATE INDEX IF NOT EXISTS idx_esbl_lab_date ON esbl_lab_results(entry_date);
CREATE INDEX IF NOT EXISTS idx_esbl_lab_organism ON esbl_lab_results(organism, antibiotic);
