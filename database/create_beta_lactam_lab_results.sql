-- ============================================================
-- Beta-Lactam Resistance Spectrum Prediction
-- Table: beta_lactam_lab_results
-- (Replaces: esbl_lab_results)
-- Stores confirmed AST results with beta-lactam generation mapping.
-- ============================================================

CREATE TABLE IF NOT EXISTS beta_lactam_lab_results (

    id SERIAL PRIMARY KEY,

    encounter_id VARCHAR(50) NOT NULL,  -- FK → beta_lactam_encounters

    -- ─────────── Patient Context (denormalized for lab queries) ───────────
    lab_no VARCHAR(50),
    age INT,
    gender VARCHAR(10),
    bht VARCHAR(50),
    ward VARCHAR(50) NOT NULL,
    specimen_type VARCHAR(50) NOT NULL,
    organism VARCHAR(100) NOT NULL,

    -- ─────────── Antibiotic & Susceptibility Result ───────────
    antibiotic VARCHAR(100) NOT NULL,   -- Full drug name, e.g. "Meropenem"
    result VARCHAR(5) NOT NULL,         -- S / I / R
    mic_value NUMERIC(8, 4),            -- Optional: MIC value from VITEK/Phoenix
    breakpoint_standard VARCHAR(20),    -- e.g. EUCAST, CLSI (optional)

    -- ─────────── Generation Classification ───────────
    generation VARCHAR(20) NOT NULL DEFAULT 'Non_BL',
    -- Mapping rules:
    --   Gen1      → Cefalexin, Cefazolin
    --   Gen2      → Cefuroxime (CXM), Cefaclor
    --   Gen3      → Ceftriaxone (CRO), Cefotaxime (CTX), Ceftazidime (CAZ)
    --   Gen4      → Cefepime (FEP)
    --   Carbapenem→ Meropenem (MEM), Imipenem (IMP), Ertapenem (ETP)
    --   BL_Combo  → Pip-Tazo (TZP), Amoxiclav (AMC)
    --   Non_BL    → Aminoglycosides, Fluoroquinolones, Nitrofurantoin, etc.

    -- ─────────── Timestamps ───────────
    entry_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_blab_encounter ON beta_lactam_lab_results(encounter_id);
CREATE INDEX IF NOT EXISTS idx_blab_date      ON beta_lactam_lab_results(entry_date);
CREATE INDEX IF NOT EXISTS idx_blab_org_abx   ON beta_lactam_lab_results(organism, antibiotic);
CREATE INDEX IF NOT EXISTS idx_blab_gen       ON beta_lactam_lab_results(generation);
CREATE INDEX IF NOT EXISTS idx_blab_result    ON beta_lactam_lab_results(result);


-- ============================================================
-- Reference Table: antibiotic_generation_map
-- Centralized lookup for antibiotic → generation classification.
-- Used by the backend service to auto-assign generation on insert.
-- ============================================================

CREATE TABLE IF NOT EXISTS antibiotic_generation_map (
    id SERIAL PRIMARY KEY,
    antibiotic_name VARCHAR(100) UNIQUE NOT NULL,   -- Full name, e.g. "Meropenem"
    antibiotic_code VARCHAR(10),                    -- Short code, e.g. "MEM"
    generation VARCHAR(20) NOT NULL,                -- Gen1 / Gen2 / Gen3 / Gen4 / Carbapenem / BL_Combo / Non_BL
    drug_class VARCHAR(50),                         -- e.g. "Carbapenem", "3rd-Gen Cephalosporin"
    is_beta_lactam BOOLEAN DEFAULT TRUE,
    notes TEXT
);

-- Standard beta-lactam reference data
INSERT INTO antibiotic_generation_map (antibiotic_name, antibiotic_code, generation, drug_class, is_beta_lactam) VALUES
    -- Generation 1
    ('Cefalexin',               'CFX',  'Gen1',       '1st-Gen Cephalosporin', TRUE),
    ('Cefazolin',               'CFZ',  'Gen1',       '1st-Gen Cephalosporin', TRUE),
    -- Generation 2
    ('Cefuroxime',              'CXM',  'Gen2',       '2nd-Gen Cephalosporin', TRUE),
    ('Cefaclor',                'CEC',  'Gen2',       '2nd-Gen Cephalosporin', TRUE),
    -- Generation 3
    ('Ceftriaxone',             'CRO',  'Gen3',       '3rd-Gen Cephalosporin', TRUE),
    ('Cefotaxime',              'CTX',  'Gen3',       '3rd-Gen Cephalosporin', TRUE),
    ('Ceftazidime',             'CAZ',  'Gen3',       '3rd-Gen Cephalosporin', TRUE),
    -- Generation 4
    ('Cefepime',                'FEP',  'Gen4',       '4th-Gen Cephalosporin', TRUE),
    -- Carbapenems
    ('Meropenem',               'MEM',  'Carbapenem', 'Carbapenem',             TRUE),
    ('Imipenem',                'IMP',  'Carbapenem', 'Carbapenem',             TRUE),
    ('Ertapenem',               'ETP',  'Carbapenem', 'Carbapenem',             TRUE),
    -- Beta-lactam Combinations
    ('Piperacillin-Tazobactam', 'TZP',  'BL_Combo',  'BL + Inhibitor',         TRUE),
    ('Pip-Tazo',                'TZP',  'BL_Combo',  'BL + Inhibitor',         TRUE),
    ('Amoxicillin-Clavulanate', 'AMC',  'BL_Combo',  'BL + Inhibitor',         TRUE),
    ('Ampicillin',              'AMP',  'BL_Combo',  'Penicillin',             TRUE),
    -- Non-beta-lactam (tracked but not scored for spectrum)
    ('Amikacin',                'AMK',  'Non_BL',    'Aminoglycoside',         FALSE),
    ('Gentamicin',              'GEN',  'Non_BL',    'Aminoglycoside',         FALSE),
    ('Ciprofloxacin',           'CIP',  'Non_BL',    'Fluoroquinolone',        FALSE),
    ('Levofloxacin',            'LVX',  'Non_BL',    'Fluoroquinolone',        FALSE),
    ('Cotrimoxazole',           'SXT',  'Non_BL',    'Folate Antagonist',      FALSE),
    ('Nitrofurantoin',          'NIT',  'Non_BL',    'Nitrofuran',             FALSE)
ON CONFLICT (antibiotic_name) DO NOTHING;
