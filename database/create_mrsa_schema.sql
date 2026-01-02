CREATE TABLE IF NOT EXISTS mrsa_raw_clean (
    id SERIAL PRIMARY KEY,
    mrsa_label INT NOT NULL, -- 1=MRSA, 0=MSSA (Derived Ground Truth)
    ward VARCHAR(50),
    age INT,
    gender VARCHAR(10),
    sample_type VARCHAR(100),
    pus_type VARCHAR(100),
    cell_count VARCHAR(100),
    gram_positivity VARCHAR(100),
    growth_time VARCHAR(100),
    bht VARCHAR(50), -- Kept for admission tracing, but PII risk if real data
    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast retrieval
CREATE INDEX IF NOT EXISTS idx_mrsa_label ON mrsa_raw_clean(mrsa_label);
CREATE INDEX IF NOT EXISTS idx_mrsa_ward ON mrsa_raw_clean(ward);
