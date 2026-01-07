-- =====================================================
-- OUTBREAK VS MODEL DRIFT DISCRIMINATOR SCHEMA
-- =====================================================
-- Purpose: Separate ward-level epidemiological events from systemic model failure
-- Governance: Prevents outbreaks from triggering inappropriate retraining

-- =====================================================
-- OUTBREAK EVENTS (Ward-Level Deviations)
-- =====================================================
CREATE TABLE IF NOT EXISTS public.stp_outbreak_events (
    outbreak_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ward VARCHAR(100) NOT NULL,
    organism VARCHAR(100) NOT NULL,
    antibiotic VARCHAR(100) NOT NULL,
    detected_week DATE NOT NULL,
    
    -- REFINEMENT #1: Model Traceability
    source_model_id UUID REFERENCES public.stp_model_registry(model_id),
    
    -- Evidence
    validation_count INTEGER NOT NULL,  -- Number of CI misses supporting outbreak
    avg_deviation FLOAT NOT NULL,  -- Average (observed - predicted)
    severity VARCHAR(10) CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH')),
    
    -- REFINEMENT #4: Human Confirmation Gate
    status VARCHAR(20) CHECK (status IN ('new', 'under_review', 'confirmed', 'false_alarm')) DEFAULT 'new',
    
    -- Governance
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_by UUID,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    
    -- REFINEMENT #3: Alert Fatigue Control (one per ward/organism/antibiotic/week)
    UNIQUE (ward, organism, antibiotic, detected_week)
);

CREATE INDEX idx_outbreak_status ON stp_outbreak_events(status);
CREATE INDEX idx_outbreak_week ON stp_outbreak_events(detected_week);
CREATE INDEX idx_outbreak_severity ON stp_outbreak_events(severity, status);

COMMENT ON TABLE stp_outbreak_events IS 'Ward-level outbreak detection - MUST NOT contribute to model drift statistics';
COMMENT ON COLUMN stp_outbreak_events.source_model_id IS 'Model that detected the deviation (audit trail)';
COMMENT ON COLUMN stp_outbreak_events.status IS 'Only "confirmed" outbreaks propagate to clinical dashboards';

-- =====================================================
-- LINK VALIDATION EVENTS TO OUTBREAKS
-- =====================================================
-- Allows exclusion of outbreak data from drift calculations
ALTER TABLE public.stp_prediction_validation_events
ADD COLUMN IF NOT EXISTS linked_outbreak_id UUID REFERENCES public.stp_outbreak_events(outbreak_id);

CREATE INDEX idx_validation_outbreak_link ON stp_prediction_validation_events(linked_outbreak_id);

COMMENT ON COLUMN stp_prediction_validation_events.linked_outbreak_id IS 'REFINEMENT #2: Outbreak-linked validations excluded from drift metrics';

-- =====================================================
-- RLS POLICIES
-- =====================================================
ALTER TABLE public.stp_outbreak_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Enable read for authenticated" ON public.stp_outbreak_events FOR SELECT USING (true);
CREATE POLICY "Enable insert for service" ON public.stp_outbreak_events FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for service" ON public.stp_outbreak_events FOR UPDATE USING (true);

-- =====================================================
-- GOVERNANCE COMPLIANCE
-- =====================================================
-- REFINEMENT #5: Post-Deployment Discrimination Between Epidemiological Events and Model Drift
-- 
-- CRITICAL SAFEGUARD: "Outbreak ≠ Drift"
-- 
-- Ward-level outbreaks MUST generate alerts but MUST NOT trigger model retraining.
-- Systemic drift across ≥3 wards MAY trigger retraining after human approval.
-- This separation prevents "learning away" epidemiological signals.
