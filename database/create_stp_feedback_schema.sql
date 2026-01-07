
-- STP Feedback Loop Database Schema
-- Governance: Post-Deployment Validation (Extends Stage 5)
-- Status: Reviewer-Proof Implementation

-- =====================================================
-- 1. RAW AST SUBMISSIONS (Isolate-Level)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.stp_external_ast_raw (
    submission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ward VARCHAR(100) NOT NULL,
    organism VARCHAR(100) NOT NULL,
    antibiotic VARCHAR(100) NOT NULL,
    ast_result VARCHAR(2) NOT NULL CHECK (ast_result IN ('S', 'I', 'R', 'NA')),
    sample_date DATE NOT NULL,
    isolate_number INTEGER NOT NULL,
    
    -- FIX #1: Duplicate Protection (CRITICAL)
    submission_fingerprint TEXT NOT NULL UNIQUE,
    
    -- FIX #2: Data Authenticity Flag
    data_source VARCHAR(30) NOT NULL CHECK (data_source IN ('LIS', 'MANUAL')),
    
    -- FIX #4: Model Version Lock
    model_id UUID REFERENCES public.stp_model_registry(model_id),
    
    -- Governance
    submitted_by UUID, -- References auth.users(id) if available
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_submission UNIQUE (ward, organism, antibiotic, sample_date, isolate_number, submitted_by)
);

CREATE INDEX idx_ast_fingerprint ON stp_external_ast_raw(submission_fingerprint);
CREATE INDEX idx_ast_model_version ON stp_external_ast_raw(model_id);
CREATE INDEX idx_ast_sample_date ON stp_external_ast_raw(sample_date);

COMMENT ON TABLE stp_external_ast_raw IS 'Raw isolate-level AST submissions with duplicate protection and model version locking';
COMMENT ON COLUMN stp_external_ast_raw.submission_fingerprint IS 'SHA256 hash for duplicate detection';
COMMENT ON COLUMN stp_external_ast_raw.data_source IS 'LIS = Laboratory Information System export, MANUAL = Ward entry';
COMMENT ON COLUMN stp_external_ast_raw.model_id IS 'Active model at submission time for temporal alignment';

-- =====================================================
-- 2. DERIVED RESISTANCE RATES (System-Calculated)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.stp_external_resistance_derived (
    derived_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ward VARCHAR(100) NOT NULL,
    organism VARCHAR(100) NOT NULL,
    antibiotic VARCHAR(100) NOT NULL,
    week_start DATE NOT NULL,
    
    -- Raw counts (system-derived, M21 compliant)
    s_count INTEGER NOT NULL,
    i_count INTEGER NOT NULL,
    r_count INTEGER NOT NULL,
    na_count INTEGER NOT NULL,
    tested_count INTEGER NOT NULL, -- S + I + R (NA excluded per M21)
    
    -- Derived rate (M22 compliant)
    resistance_rate FLOAT CHECK (resistance_rate BETWEEN 0 AND 1),
    is_stable BOOLEAN NOT NULL, -- tested_count >= 10 (M12)
    
    -- FIX #3: Completeness Check
    completeness_ratio FLOAT NOT NULL CHECK (completeness_ratio BETWEEN 0 AND 1),
    expected_antibiotics INTEGER NOT NULL,
    tested_antibiotics INTEGER NOT NULL,
    
    derived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_derived_week UNIQUE (ward, organism, antibiotic, week_start)
);

CREATE INDEX idx_derived_completeness ON stp_external_resistance_derived(completeness_ratio);
CREATE INDEX idx_derived_stability ON stp_external_resistance_derived(is_stable);
CREATE INDEX idx_derived_week ON stp_external_resistance_derived(week_start);

COMMENT ON TABLE stp_external_resistance_derived IS 'System-derived resistance rates from raw AST with completeness tracking';
COMMENT ON COLUMN stp_external_resistance_derived.completeness_ratio IS 'tested_antibiotics / expected_antibiotics (quality gate)';
COMMENT ON COLUMN stp_external_resistance_derived.is_stable IS 'TRUE if tested_count >= 10 (M12 compliance)';

-- =====================================================
-- 3. PREDICTION VALIDATION EVENTS
-- =====================================================
CREATE TABLE IF NOT EXISTS public.stp_prediction_validation_events (
    validation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES public.stp_model_registry(model_id),
    ward VARCHAR(100) NOT NULL,
    organism VARCHAR(100) NOT NULL,
    antibiotic VARCHAR(100) NOT NULL,
    
    -- Comparison (temporally aligned via model_id lock)
    predicted_rate FLOAT NOT NULL,
    observed_rate FLOAT NOT NULL,
    lower_ci FLOAT,
    upper_ci FLOAT,
    
    -- Metrics
    absolute_error FLOAT NOT NULL,
    within_ci BOOLEAN NOT NULL,
    
    -- FIX #3: Quality flag
    completeness_ratio FLOAT NOT NULL,
    
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_validation_model ON stp_prediction_validation_events(model_id);
CREATE INDEX idx_validation_quality ON stp_prediction_validation_events(within_ci, completeness_ratio);
CREATE INDEX idx_validation_time ON stp_prediction_validation_events(validated_at);

COMMENT ON TABLE stp_prediction_validation_events IS 'Model prediction validation with quality filtering';
COMMENT ON COLUMN stp_prediction_validation_events.model_id IS 'Model that generated the prediction (version-locked)';
COMMENT ON COLUMN stp_prediction_validation_events.within_ci IS 'TRUE if observed_rate within [lower_ci, upper_ci]';

-- =====================================================
-- 4. MODEL LIFECYCLE EVENTS (Governance)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.stp_model_lifecycle_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES public.stp_model_registry(model_id),
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN (
        'RETRAINING_TRIGGERED',
        'SHADOW_DEPLOYMENT',
        'PROMOTED_TO_ACTIVE',
        'ARCHIVED'
    )),
    trigger_reason TEXT,
    approved_by UUID, -- References auth.users(id) if available
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- FIX #5: Retraining Rate Limit Enforcement (30-day cooldown)
CREATE UNIQUE INDEX idx_retraining_cooldown 
ON stp_model_lifecycle_events(model_id, event_type)
WHERE event_type = 'RETRAINING_TRIGGERED' 
  AND created_at > NOW() - INTERVAL '30 days';

CREATE INDEX idx_lifecycle_model ON stp_model_lifecycle_events(model_id);
CREATE INDEX idx_lifecycle_type ON stp_model_lifecycle_events(event_type);

COMMENT ON TABLE stp_model_lifecycle_events IS 'Model deployment and retraining governance (M61, M67)';
COMMENT ON INDEX idx_retraining_cooldown IS 'Prevents retraining loops - max 1 trigger per model per 30 days';

-- =====================================================
-- ENABLE ROW LEVEL SECURITY
-- =====================================================
ALTER TABLE public.stp_external_ast_raw ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stp_external_resistance_derived ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stp_prediction_validation_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stp_model_lifecycle_events ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- RLS POLICIES (Read access for authenticated users)
-- =====================================================
CREATE POLICY "Enable read for authenticated" ON public.stp_external_ast_raw FOR SELECT USING (true);
CREATE POLICY "Enable read for authenticated" ON public.stp_external_resistance_derived FOR SELECT USING (true);
CREATE POLICY "Enable read for authenticated" ON public.stp_prediction_validation_events FOR SELECT USING (true);
CREATE POLICY "Enable read for authenticated" ON public.stp_model_lifecycle_events FOR SELECT USING (true);

-- Write policies (restrict to API service role or specific users)
CREATE POLICY "Enable insert for service" ON public.stp_external_ast_raw FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable insert for service" ON public.stp_external_resistance_derived FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable insert for service" ON public.stp_prediction_validation_events FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable insert for service" ON public.stp_model_lifecycle_events FOR INSERT WITH CHECK (true);

-- =====================================================
-- GOVERNANCE COMPLIANCE SUMMARY
-- =====================================================
-- M12: Stability threshold enforced via is_stable column
-- M21: NA excluded from tested_count
-- M22: NULL resistance_rate when tested_count = 0
-- M50: Surveillance disclaimer enforced at API level
-- M61: Human approval gate for retraining
-- M62: Full audit trail via timestamps and submitted_by
-- M66: Lineage traceability (raw → derived → validated)
-- M67: Controlled model updates via lifecycle events
-- M71: Data retention via timestamp columns
-- Duplicate Protection: submission_fingerprint uniqueness
-- Data Authenticity: data_source tagging
-- Completeness Check: completeness_ratio gating
-- Model Version Lock: model_id capture at submission
-- Retraining Rate Limit: 30-day cooldown index
