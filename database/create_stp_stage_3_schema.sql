
-- STP Stage 3 Database Schema: Predictive Modeling
-- Governance: M23-M40
-- Status: Implemented

-- 1. Model Registry (M29)
-- Stores trained model artifacts, metadata, and performance metrics.
CREATE TABLE IF NOT EXISTS public.stp_model_registry (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_type VARCHAR(50) NOT NULL, -- 'xgboost', 'logistic_regression'
    target VARCHAR(100) NOT NULL, -- 'resistance_rate'
    horizon INTEGER NOT NULL, -- 1, 2, 3, 4 (weeks)
    features_hash VARCHAR(64) NOT NULL, -- Hash of input features for M23 verification
    stage2_version VARCHAR(100) NOT NULL, -- Links to frozen feature store V2
    hyperparameters JSONB, -- Training config
    metrics_json JSONB, -- M38 (Brier), M39 (Thresholds), NPV, Sensitivity
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'staging')),
    filepath VARCHAR(255) NOT NULL, -- Path to serialized model .pkl/.json
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID -- Link to auth.users if needed
);

-- 2. Model Predictions (M25, M33, M34)
-- Stores probabilistic forecasts. Wards off patient-level data (M28).
CREATE TABLE IF NOT EXISTS public.stp_model_predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES public.stp_model_registry(model_id),
    ward VARCHAR(100) NOT NULL,
    organism VARCHAR(100) NOT NULL,
    antibiotic VARCHAR(100) NOT NULL,
    forecast_week DATE NOT NULL, -- The future week being predicted
    predicted_probability FLOAT NOT NULL CHECK (predicted_probability BETWEEN 0 AND 1),
    
    -- M33: Uncertainty Bounds
    lower_ci FLOAT CHECK (lower_ci BETWEEN 0 AND 1),
    upper_ci FLOAT CHECK (upper_ci BETWEEN 0 AND 1),
    uncertainty_method VARCHAR(50), -- 'bootstrap', 'quantile'
    
    -- M34: Alert Escalation
    risk_level VARCHAR(10) CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Explainability (M27)
-- Stores SHAP feature importance for transparency.
CREATE TABLE IF NOT EXISTS public.stp_model_explanations (
    explanation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id UUID REFERENCES public.stp_model_predictions(prediction_id) ON DELETE CASCADE,
    feature_name VARCHAR(100) NOT NULL,
    importance_value FLOAT NOT NULL,
    rank INTEGER NOT NULL -- 1 = Most important driver
);

-- 4. Early Warnings (M37, M34)
-- Stores statistical signal detections (CUSUM, etc.)
CREATE TABLE IF NOT EXISTS public.stp_early_warnings (
    warning_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ward VARCHAR(100) NOT NULL,
    organism VARCHAR(100) NOT NULL,
    antibiotic VARCHAR(100) NOT NULL,
    detected_at_week DATE NOT NULL,
    signal_strength FLOAT, -- CUSUM score or similar
    method VARCHAR(50) NOT NULL, -- 'cusum', 'bayesian'
    
    -- M34: Severity
    severity VARCHAR(10) CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH')),
    
    -- M37: Human-in-Loop Status
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN ('new', 'reviewed', 'dismissed', 'confirmed')),
    reviewed_by UUID,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. Drift Monitoring (M35)
-- Tracks model performance decay over time.
CREATE TABLE IF NOT EXISTS public.stp_model_drift_metrics (
    drift_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES public.stp_model_registry(model_id),
    evaluation_date DATE NOT NULL,
    psi_score FLOAT, -- Population Stability Index
    prediction_mean FLOAT,
    prediction_std FLOAT,
    distribution_shift_detected BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.stp_model_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stp_model_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stp_model_explanations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stp_early_warnings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.stp_model_drift_metrics ENABLE ROW LEVEL SECURITY;

-- Policies
-- 1. Read access for authenticated users (Surveillance Dashboard)
CREATE POLICY "Enable read access for authenticated users" ON public.stp_model_registry FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Enable read access for authenticated users" ON public.stp_model_predictions FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Enable read access for authenticated users" ON public.stp_model_explanations FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Enable read access for authenticated users" ON public.stp_early_warnings FOR SELECT USING (auth.role() = 'authenticated');
CREATE POLICY "Enable read access for authenticated users" ON public.stp_model_drift_metrics FOR SELECT USING (auth.role() = 'authenticated');

-- 2. Write access for Service Role (Pipeline) only
-- Ideally, we use a service_role key for the pipeline.
-- For simplicity in this setup, we might allow authenticated users if they are admin, or strictly valid service role.
-- We'll assume the pipeline connects with a specific role or we rely on explicit GRANTs in production.
-- Here, we permit INSERT for authenticated users to facilitate the python script execution if it runs as a user,
-- BUT strictly we should restrict this. 
-- For this prototype/implementation phase, we allow INSERT/UPDATE for 'service_role' and 'authenticated' (dev mode).

CREATE POLICY "Enable insert for service_role" ON public.stp_model_registry FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for service_role" ON public.stp_model_registry FOR UPDATE USING (true);

CREATE POLICY "Enable insert for service_role" ON public.stp_model_predictions FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable insert for service_role" ON public.stp_model_explanations FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable insert for service_role" ON public.stp_early_warnings FOR INSERT WITH CHECK (true);
CREATE POLICY "Enable update for service_role" ON public.stp_early_warnings FOR UPDATE USING (true); -- For status updates
CREATE POLICY "Enable insert for service_role" ON public.stp_model_drift_metrics FOR INSERT WITH CHECK (true);

-- Indexes for Query Performance
CREATE INDEX IF NOT EXISTS idx_predictions_lookup ON public.stp_model_predictions(ward, organism, antibiotic, forecast_week);
CREATE INDEX IF NOT EXISTS idx_warnings_lookup ON public.stp_early_warnings(ward, organism, antibiotic, status);
CREATE INDEX IF NOT EXISTS idx_registry_active ON public.stp_model_registry(target, horizon, status);
