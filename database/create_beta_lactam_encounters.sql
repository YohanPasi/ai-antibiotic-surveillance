-- ============================================================
-- Beta-Lactam Resistance Spectrum Prediction
-- Table: beta_lactam_encounters
-- (Replaces: esbl_encounters)
-- Stores patient day-0 inputs and full spectrum prediction.
-- ============================================================

CREATE TABLE IF NOT EXISTS beta_lactam_encounters (

    -- Primary Key
    encounter_id VARCHAR(50) PRIMARY KEY,

    -- ─────────── Patient Demographics ───────────
    age INT,
    gender VARCHAR(10),
    ward VARCHAR(100),

    -- ─────────── Microbiology (Day-0 Features) ───────────
    organism VARCHAR(200) NOT NULL,
    gram_stain VARCHAR(10),           -- Always 'GNB' for Enterobacterales scope
    sample_type VARCHAR(100),
    cell_count_level VARCHAR(20),     -- Low / Moderate / High
    pus_type VARCHAR(20),             -- Abscess / Wound_Pus / ET_Secretion / NA
    pure_growth VARCHAR(20),          -- Pure / Mixed

    -- ─────────── Spectrum Prediction (Core Output) ───────────
    predicted_beta_lactam_spectrum JSONB,
    -- JSON shape per generation:
    -- {
    --   "Gen1":      { "probability": 0.85, "traffic_light": "Green" },
    --   "Gen2":      { "probability": 0.68, "traffic_light": "Amber" },
    --   "Gen3":      { "probability": 0.20, "traffic_light": "Red"   },
    --   "Gen4":      { "probability": 0.72, "traffic_light": "Amber" },
    --   "Carbapenem":{ "probability": 0.95, "traffic_light": "Green" },
    --   "BL_Combo":  { "probability": 0.77, "traffic_light": "Amber" }
    -- }

    top_generation_recommendation VARCHAR(50),
    -- Best generation to use empirically, e.g. "Gen1", "Carbapenem"

    predicted_success_probability NUMERIC(5, 4),
    -- Probability that top_generation_recommendation will succeed (0.0000–1.0000)

    -- ─────────── OOD & Explainability ───────────
    spectrum_ood_warning BOOLEAN DEFAULT FALSE,
    -- True if day-0 inputs fall outside the model's training distribution

    top_feature_influences JSONB,
    -- SHAP top-3 feature array for audit/transparency
    -- e.g. [{"feature": "Ward_ICU", "shap_value": 0.32, "direction": "increases_resistance"}, ...]

    -- ─────────── Model Provenance ───────────
    model_version VARCHAR(50),
    evidence_version VARCHAR(50),     -- Version of outcome tables used for scoring

    -- ─────────── Recommendations (Full Ranked List) ───────────
    recommendations JSONB,
    -- Array of scored generations/drugs:
    -- [{ "generation": "Gen1", "success_prob": 0.85, "score": 0.85, "stewardship_note": "Preferred" }, ...]

    -- ─────────── Lifecycle Status ───────────
    status VARCHAR(20) DEFAULT 'PENDING',
    -- PENDING → Empiric prediction made, awaiting AST
    -- COMPLETED → Confirmatory AST results received

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_blenc_organism  ON beta_lactam_encounters(organism);
CREATE INDEX IF NOT EXISTS idx_blenc_ward      ON beta_lactam_encounters(ward);
CREATE INDEX IF NOT EXISTS idx_blenc_top_gen   ON beta_lactam_encounters(top_generation_recommendation);
CREATE INDEX IF NOT EXISTS idx_blenc_date      ON beta_lactam_encounters(created_at);
CREATE INDEX IF NOT EXISTS idx_blenc_status    ON beta_lactam_encounters(status);
