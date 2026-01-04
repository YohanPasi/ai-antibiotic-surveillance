DROP TABLE IF EXISTS master_definitions CASCADE;

CREATE TABLE IF NOT EXISTS master_definitions (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL, -- 'WARD', 'SAMPLE_TYPE', 'GENDER'
    label VARCHAR(100) NOT NULL, -- Display Name
    value VARCHAR(100) NOT NULL, -- System Value
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, value)
);

-- Seed Wards (Matches Random Forest Model Categories)
INSERT INTO master_definitions (category, label, value) VALUES
('WARD', 'ICU', 'ICU'),
('WARD', 'Ward 01', 'Ward 01'),
('WARD', 'Ward 02', 'Ward 02'),
('WARD', 'OPD', 'Opd'),
('WARD', 'A&E', 'A&E'),
('WARD', 'O/C', 'O/C'),
('WARD', 'Other', 'Other')
ON CONFLICT DO NOTHING;

-- Seed Sample Types
INSERT INTO master_definitions (category, label, value) VALUES
('SAMPLE_TYPE', 'Blood', 'Blood'),
('SAMPLE_TYPE', 'Urine', 'Urine'),
('SAMPLE_TYPE', 'Pus/Wound', 'Pus/Wound'),
('SAMPLE_TYPE', 'Sputum', 'Sputum'),
('SAMPLE_TYPE', 'Other', 'Other')
ON CONFLICT DO NOTHING;

-- Seed Gram Stain
INSERT INTO master_definitions (category, label, value) VALUES
('GRAM_STAIN', 'GPC (Cocci)', 'GPC'),
('GRAM_STAIN', 'Unknown', 'Unknown')
ON CONFLICT DO NOTHING;
