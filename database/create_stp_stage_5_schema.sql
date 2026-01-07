
-- STP Stage 5: Operational Schema
-- Governance: M56-M75 (Operational Safety & Lifecycle)

-- 1. Live Predictions (The "Hot" Table)
-- Stores recent inference results for driving alerts/dashboards.
CREATE TABLE IF NOT EXISTS public.stp_live_predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES public.stp_model_registry(model_id),
    dataset_hash VARCHAR(64) NOT NULL, -- Traceability (M66)
    ward VARCHAR(100) NOT NULL,
    organism VARCHAR(100) NOT NULL,
    antibiotic VARCHAR(100) NOT NULL,
    prediction_date DATE NOT NULL DEFAULT CURRENT_DATE, -- The 'T' moment
    horizon_date DATE NOT NULL, -- The 'T+h' target
    predicted_prob FLOAT NOT NULL,
    uncertainty_score FLOAT, -- From Stage 3 engine
    risk_level VARCHAR(20), -- 'low', 'medium', 'high'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    retention_expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 months'), -- M71
    
    -- Cleanups needed on model_id? No, we keep history even if model archived.
    CONSTRAINT fk_model FOREIGN KEY (model_id) REFERENCES public.stp_model_registry(model_id)
);

-- 2. Audit Log (The "Cold" Immutable Ledger) -> M62
-- Logs every single inference event for compliance.
CREATE TABLE IF NOT EXISTS public.stp_prediction_audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID REFERENCES public.stp_live_predictions(prediction_id),
    model_id UUID NOT NULL,
    input_features_json JSONB, -- Full input vector snapshot
    execution_time_ms INTEGER, -- M68 SLA
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    retention_expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '24 months') -- M71
);

-- 3. Alert Management (M60, M61)
CREATE TABLE IF NOT EXISTS public.stp_alert_events (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID REFERENCES public.stp_live_predictions(prediction_id),
    alert_type VARCHAR(50) NOT NULL, -- 'high_risk', 'drift_warning'
    severity VARCHAR(20) NOT NULL, -- 'info', 'warning', 'critical'
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.stp_alert_reviews (
    review_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID REFERENCES public.stp_alert_events(alert_id),
    reviewed_by UUID, -- Link to user system if available, else UUID
    action VARCHAR(50) NOT NULL, -- 'acknowledged', 'dismissed', 'escalated'
    comments TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Drift & Performance Metrics (M58, M59, M57)
CREATE TABLE IF NOT EXISTS public.stp_drift_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    window_date DATE NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- 'psi_features', 'kl_predictions', 'rolling_npv'
    metric_value FLOAT NOT NULL,
    status VARCHAR(20) DEFAULT 'ok', -- 'ok', 'warning', 'critical'
    details_json JSONB, -- specific features causing drift
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Lifecycle Events (M63, M64, M65)
CREATE TABLE IF NOT EXISTS public.stp_model_lifecycle_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES public.stp_model_registry(model_id),
    event_type VARCHAR(50) NOT NULL, -- 'activated', 'deactivated', 'retraining_triggered'
    triggered_by VARCHAR(50) NOT NULL, -- 'user', 'system_drift', 'schedule'
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Incident Events (M72) - NEW
CREATE TABLE IF NOT EXISTS public.stp_incident_events (
    incident_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_type VARCHAR(50) NOT NULL, -- 'DRIFT', 'PERFORMANCE', 'SYSTEM'
    severity VARCHAR(20) NOT NULL, -- 'LOW', 'MED', 'HIGH'
    description TEXT NOT NULL,
    triggered_by VARCHAR(100), -- 'drift_monitor_job'
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. Governance Approvals (M74) - NEW
CREATE TABLE IF NOT EXISTS public.stp_governance_approvals (
    approval_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_id UUID NOT NULL, -- Can be model_id or incident_id
    target_type VARCHAR(50) NOT NULL, -- 'MODEL', 'INCIDENT'
    approved_by_user VARCHAR(100), -- Name/ID
    approval_type VARCHAR(50) NOT NULL, -- 'ACTIVATION', 'RETIREMENT', 'INCIDENT_CLOSE'
    signature_hash VARCHAR(128), -- Cryptographic proof placeholder
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. Updates to Existing Registry (M73)
-- We need to add 'deployment_mode' via ALTER TABLE if not exists.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='stp_model_registry' AND column_name='deployment_mode') THEN
        ALTER TABLE public.stp_model_registry ADD COLUMN deployment_mode VARCHAR(20) DEFAULT 'SHADOW';
        -- Valid modes: ACTIVE, SHADOW, RETIRED
    END IF;
END $$;
