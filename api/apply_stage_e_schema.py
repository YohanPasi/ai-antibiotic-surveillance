import os
from sqlalchemy import create_engine, text

# Get DB URL from env
DATABASE_URL = os.getenv("DATABASE_URL")

def apply_schema():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not set.")
        return

    print("🔌 Connecting to Database...")
    engine = create_engine(DATABASE_URL)
    
    # Embedded SQL for Stage E Schema
    sql_content = """
-- Stage E: Performance & Governance Schema

-- 1. Performance Snapshots (Aggregated Metrics)
CREATE TABLE IF NOT EXISTS mrsa_performance_snapshots (
    id SERIAL PRIMARY KEY,
    snapshot_date TIMESTAMP DEFAULT NOW(),
    window_type VARCHAR(20) NOT NULL, -- '7d', '30d', 'baseline'
    
    -- Metrics
    total_predictions INT DEFAULT 0,
    accuracy FLOAT DEFAULT 0.0,
    sensitivity FLOAT DEFAULT 0.0,
    specificity FLOAT DEFAULT 0.0,
    npv FLOAT DEFAULT 0.0,
    ppv FLOAT DEFAULT 0.0,
    
    -- Counts
    true_positives INT DEFAULT 0,
    true_negatives INT DEFAULT 0,
    false_positives INT DEFAULT 0,
    false_negatives INT DEFAULT 0,
    
    -- Stewardship
    vanco_days_saved_est FLOAT DEFAULT 0.0,
    
    -- Deep Dive
    model_metrics JSONB, -- Stores per-model stats
    baseline_version VARCHAR(50) -- e.g. 'v1.0'
);

CREATE INDEX IF NOT EXISTS idx_perf_window ON mrsa_performance_snapshots(window_type, snapshot_date);

-- 2. Governance Decision Log
CREATE TABLE IF NOT EXISTS mrsa_governance_decisions (
    id SERIAL PRIMARY KEY,
    decision_date TIMESTAMP DEFAULT NOW(),
    triggered_by VARCHAR(255), -- Reason (e.g. 'NPV Drop')
    decision VARCHAR(50) NOT NULL, -- 'MONITOR', 'RETRAIN_REVIEW', 'DISABLE_MODULE'
    decided_by VARCHAR(100), -- Admin Username
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_gov_date ON mrsa_governance_decisions(decision_date);
    """
    
    with engine.connect() as conn:
        print("⚡ Applying Stage E Schema...")
        # Split by ; for safety if simple execute doesn't handle multiple
        # But SQLAlchemy usually handles block if passed properly. Text() is safer for scripts.
        conn.execute(text(sql_content))
        conn.commit()
        print("✅ Stage E Schema Applied Successfully.")

if __name__ == "__main__":
    apply_schema()
