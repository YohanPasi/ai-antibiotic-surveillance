-- ============================================================
-- Beta-Lactam Resistance Spectrum Prediction
-- Table: beta_lactam_audit_logs
-- (Replaces: esbl_audit_logs)
-- Immutable governance trail for every spectrum prediction.
-- ============================================================

CREATE TABLE IF NOT EXISTS beta_lactam_audit_logs (

    id SERIAL PRIMARY KEY,
    log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    encounter_id VARCHAR(50),           -- FK → beta_lactam_encounters

    -- ─────────── Patient Context ───────────
    ward VARCHAR(100),
    organism VARCHAR(200) NOT NULL,
    age INT,
    gender VARCHAR(10),
    sample_type VARCHAR(50),

    -- ─────────── Full Spectrum Prediction ───────────
    predicted_beta_lactam_spectrum JSONB,
    -- Complete per-generation prediction at time of decision
    -- Stored immutably for audit reconstruction

    -- ─────────── Summary Fields (for quick queries / dashboard) ───────────
    top_generation_recommendation VARCHAR(50),
    -- e.g. "Gen1", "Carbapenem"

    traffic_light_summary VARCHAR(10),
    -- Worst-case traffic light across all generations: Green / Amber / Red

    predicted_success_probability NUMERIC(5, 2),
    -- Predicted success likelihood for the top recommendation

    -- ─────────── Explainability ───────────
    top_feature_influences JSONB,
    -- SHAP top-3 features that drove this prediction

    -- ─────────── Safety & OOD ───────────
    model_version VARCHAR(50),
    ood_detected BOOLEAN DEFAULT FALSE,

    -- ─────────── Clinician Decision (Post-Recommendation) ───────────
    clinician_override VARCHAR(10),
    -- 'ACCEPT' — clinician followed the top recommendation
    -- 'OVERRIDE' — clinician deviated from the recommendation
    -- NULL — decision not yet logged

    override_reason TEXT,
    -- Mandatory free-text reason if clinician_override = 'OVERRIDE'

    -- ─────────── Governance ───────────
    governance_note TEXT
    -- Free-text notes for stewardship team review
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_blaudit_encounter ON beta_lactam_audit_logs(encounter_id);
CREATE INDEX IF NOT EXISTS idx_blaudit_date      ON beta_lactam_audit_logs(log_date);
CREATE INDEX IF NOT EXISTS idx_blaudit_top_gen   ON beta_lactam_audit_logs(top_generation_recommendation);
CREATE INDEX IF NOT EXISTS idx_blaudit_override  ON beta_lactam_audit_logs(clinician_override);
CREATE INDEX IF NOT EXISTS idx_blaudit_ward      ON beta_lactam_audit_logs(ward);
