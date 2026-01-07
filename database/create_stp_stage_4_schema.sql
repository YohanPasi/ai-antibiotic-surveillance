
-- STP Stage 4: Model Evaluation & Clinical Validation Schema
-- Governance: M41-M55
-- Objectives: Store evaluation metadata, metrics, calibration data, and failure logs.

-- 1. Evaluation Runs (Metadata)
-- Stores distinct backtesting events.
-- M41: Links to stp_model_registry.
-- M42: Defines the specific time window used for prospective calculation.
CREATE TABLE IF NOT EXISTS stp_model_evaluation_runs (
    evaluation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES stp_model_registry(model_id),
    run_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    evaluation_window_start DATE NOT NULL,
    evaluation_window_end DATE NOT NULL,
    horizon_weeks INTEGER NOT NULL, -- M43: Horizon Specificity
    dataset_version TEXT NOT NULL, -- Link to Stage 2 Version
    status TEXT DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Model Metrics (The Scorecard)
-- Stores aggregated performance metrics.
-- M44: Metric Priority (NPV, Sensitivity, etc.)
-- M45: Ward Stratification (ward_group)
-- M51: Baseline Parity (model_type = 'baseline')
-- M52: Calibration Impact (calibration_state = 'raw' vs 'calibrated')
-- M53: Error Cost (clinical_cost_score)
CREATE TABLE IF NOT EXISTS stp_model_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES stp_model_evaluation_runs(evaluation_id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL, -- e.g., 'NPV', 'Sensitivity', 'Brier_Score'
    value NUMERIC NOT NULL,
    ward_group TEXT DEFAULT 'ALL', -- 'ALL', 'ICU', 'NON_ICU' (M45)
    model_type TEXT DEFAULT 'ml', -- 'ml' or 'baseline' (M51)
    calibration_state TEXT DEFAULT 'calibrated', -- 'raw' or 'calibrated' (M52)
    clinical_cost_score NUMERIC, -- Optional cost-weighted score (M53)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Calibration Results (Reliability Curves)
-- M46: Stores binned observed vs predicted probabilities.
CREATE TABLE IF NOT EXISTS stp_calibration_results (
    calibration_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES stp_model_evaluation_runs(evaluation_id) ON DELETE CASCADE,
    bin_index INTEGER NOT NULL, -- e.g., 0-9 for deciles
    predicted_prob_mean NUMERIC NOT NULL,
    observed_rate NUMERIC NOT NULL,
    sample_count INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Failure Cases (Audit Log)
-- M48: Explicit logging of False Negatives.
CREATE TABLE IF NOT EXISTS stp_failure_cases (
    failure_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES stp_model_evaluation_runs(evaluation_id) ON DELETE CASCADE,
    ward TEXT NOT NULL,
    organism TEXT NOT NULL,
    antibiotic TEXT NOT NULL,
    week_date DATE NOT NULL,
    predicted_prob NUMERIC NOT NULL,
    actual_outcome INTEGER NOT NULL,
    failure_type TEXT NOT NULL, -- 'FN' (False Negative) or 'FP' (False Positive)
    reason TEXT, -- 'low_n', 'boundary_case', 'drift_suspected'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. SHAP Stability Metrics (M54)
-- Stores consistency of feature importance over time.
CREATE TABLE IF NOT EXISTS stp_shap_stability_metrics (
    stability_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES stp_model_evaluation_runs(evaluation_id) ON DELETE CASCADE,
    comparison_window_start DATE NOT NULL, -- Previous window compared against
    jaccard_index NUMERIC NOT NULL, -- Similarity of top-k features
    top_features_list JSONB, -- The features that *were* stable (JSON array)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RLS Policies (Security)
-- Pipeline (Service Role) needs Write access.
-- Users need Read-Only access.

ALTER TABLE stp_model_evaluation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE stp_model_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE stp_calibration_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE stp_failure_cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE stp_shap_stability_metrics ENABLE ROW LEVEL SECURITY;

-- Policy: Allow read access to authenticated users
CREATE POLICY "Enable read access for authenticated users" ON stp_model_evaluation_runs FOR SELECT TO authenticated USING (true);
CREATE POLICY "Enable read access for authenticated users" ON stp_model_metrics FOR SELECT TO authenticated USING (true);
CREATE POLICY "Enable read access for authenticated users" ON stp_calibration_results FOR SELECT TO authenticated USING (true);
CREATE POLICY "Enable read access for authenticated users" ON stp_failure_cases FOR SELECT TO authenticated USING (true);
CREATE POLICY "Enable read access for authenticated users" ON stp_shap_stability_metrics FOR SELECT TO authenticated USING (true);

-- Policy: Allow all access to service_role (Pipeline)
CREATE POLICY "Enable all access for service role" ON stp_model_evaluation_runs FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Enable all access for service role" ON stp_model_metrics FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Enable all access for service role" ON stp_calibration_results FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Enable all access for service role" ON stp_failure_cases FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "Enable all access for service role" ON stp_shap_stability_metrics FOR ALL TO service_role USING (true) WITH CHECK (true);
