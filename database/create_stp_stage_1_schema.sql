-- =====================================================
-- STP Stage 1: Data Foundation & Governance Layer
-- Database Schema for Supabase PostgreSQL
-- =====================================================
-- Version: 1.0.0
-- Created: 2026-01-06
-- Purpose: Research-grade data governance for Streptococcus + Enterococcus surveillance
--
-- Tables:
--   1. stp_organism_taxonomy      - Canonical organism names & normalization
--   2. stp_ward_taxonomy          - Standardized ward names
--   3. stp_antibiotic_registry    - Data-driven antibiotic coverage
--   4. stp_raw_wide              - Validated wide-format AST data
--   5. stp_canonical_long        - Analysis-ready long format (MAIN OUTPUT)
--   6. stp_data_quality_log      - Audit trail of rejections
--   7. stp_dataset_metadata      - Versioning, provenance, freeze status (M5, M6)
--   8. stp_governance_declarations - Ethics & methodology (M1-M10, O1-O2)
--   9. stp_column_provenance     - Column lineage tracking (M7)
--  10. stp_stage1_readonly (VIEW) - Read-only access for Stage 2+ (M10)
--
-- Governance Components:
--   M1: Episode governance policy
--   M2: AST panel heterogeneity acknowledgment
--   M3: Temporal density validation
--   M4: Negative control declaration
--   M5: Migration version tracking
--   M6: Dataset freeze & immutability
--   M7: Column provenance registry
--   M8: RLS policies (separate file)
--   M9: Clinical non-decision disclaimer
--   M10: Stage boundary enforcement
-- =====================================================

-- Drop existing tables (CAUTION: Use only in development)
-- DROP TABLE IF EXISTS stp_canonical_long CASCADE;
-- DROP TABLE IF EXISTS stp_raw_wide CASCADE;
-- DROP TABLE IF EXISTS stp_data_quality_log CASCADE;
-- DROP TABLE IF EXISTS stp_antibiotic_registry CASCADE;
-- DROP TABLE IF EXISTS stp_organism_taxonomy CASCADE;
-- DROP TABLE IF EXISTS stp_ward_taxonomy CASCADE;
-- DROP TABLE IF EXISTS stp_dataset_metadata CASCADE;
-- DROP TABLE IF EXISTS stp_governance_declarations CASCADE;
-- DROP TABLE IF EXISTS stp_column_provenance CASCADE;

-- =====================================================
-- TABLE 1: Organism Taxonomy (Normalization Layer)
-- =====================================================
-- Purpose: Canonical organism names for normalization
-- M7: Column provenance tracked

CREATE TABLE IF NOT EXISTS stp_organism_taxonomy (
    id SERIAL PRIMARY KEY,
    canonical_name VARCHAR(200) NOT NULL UNIQUE,
    synonyms TEXT[],  -- Array of alternate names
    organism_group VARCHAR(100) DEFAULT 'Gram-Positive Cocci',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE stp_organism_taxonomy IS 'Canonical organism names for STP surveillance (M7: column provenance)';
COMMENT ON COLUMN stp_organism_taxonomy.canonical_name IS 'Official organism name used throughout system';
COMMENT ON COLUMN stp_organism_taxonomy.synonyms IS 'Array of alternate spellings/abbreviations';

-- Seed canonical organisms
INSERT INTO stp_organism_taxonomy (canonical_name, synonyms, organism_group) VALUES
('Streptococcus pneumoniae', ARRAY['S. pneumoniae', 'Strep. pneumoniae', 'Pneumococcus'], 'Gram-Positive Cocci'),
('Streptococcus agalactiae', ARRAY['S. agalactiae', 'Strep. agalactiae', 'GBS', 'Group B Strep'], 'Gram-Positive Cocci'),
('Viridans streptococci', ARRAY['Viridans strep', 'Viridans group', 'Viridans Streptococcus'], 'Gram-Positive Cocci'),
('Enterococcus faecalis', ARRAY['E. faecalis'], 'Gram-Positive Cocci'),
('Enterococcus faecium', ARRAY['E. faecium'], 'Gram-Positive Cocci')
ON CONFLICT (canonical_name) DO NOTHING;

CREATE INDEX idx_stp_organism_canonical ON stp_organism_taxonomy(canonical_name);

-- =====================================================
-- TABLE 2: Ward Taxonomy (Standardization Layer)
-- =====================================================
-- Purpose: Standardized ward names with ICU classification
-- Initialized from existing master_definitions

CREATE TABLE IF NOT EXISTS stp_ward_taxonomy (
    id SERIAL PRIMARY KEY,
    ward_name VARCHAR(100) NOT NULL UNIQUE,
    is_icu BOOLEAN DEFAULT FALSE,
    specialty_group VARCHAR(100),  -- e.g., 'Medical', 'Surgical', 'Emergency'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE stp_ward_taxonomy IS 'Standardized ward names for STP surveillance';
COMMENT ON COLUMN stp_ward_taxonomy.is_icu IS 'ICU vs non-ICU classification';
COMMENT ON COLUMN stp_ward_taxonomy.specialty_group IS 'Ward functional grouping (O2: may evolve over time)';

CREATE INDEX idx_stp_ward_name ON stp_ward_taxonomy(ward_name);
CREATE INDEX idx_stp_ward_icu ON stp_ward_taxonomy(is_icu);

-- Note: Ward data will be initialized via separate script from master_definitions

-- =====================================================
-- TABLE 3: Antibiotic Registry (Data-Driven)
-- =====================================================
-- Purpose: Track which antibiotics are tested (no cherry-picking)

CREATE TABLE IF NOT EXISTS stp_antibiotic_registry (
    id SERIAL PRIMARY KEY,
    antibiotic_name VARCHAR(100) NOT NULL,
    test_count INTEGER DEFAULT 0,
    coverage_percent NUMERIC(5,2),  -- Percentage of isolates tested
    first_seen DATE,
    last_seen DATE,
    dataset_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(antibiotic_name, dataset_version)
);

COMMENT ON TABLE stp_antibiotic_registry IS 'Data-driven antibiotic coverage (prevents cherry-picking)';
COMMENT ON COLUMN stp_antibiotic_registry.test_count IS 'Number of isolates tested with this antibiotic';
COMMENT ON COLUMN stp_antibiotic_registry.coverage_percent IS 'Percentage of total isolates tested';

CREATE INDEX idx_stp_antibiotic_name ON stp_antibiotic_registry(antibiotic_name);
CREATE INDEX idx_stp_antibiotic_version ON stp_antibiotic_registry(dataset_version);

-- =====================================================
-- TABLE 4: Dataset Metadata (Versioning & Provenance)
-- =====================================================
-- Purpose: Track dataset versions, provenance, freeze status
-- M5: Migration versioning
-- M6: Dataset freeze policy

CREATE TABLE IF NOT EXISTS stp_dataset_metadata (
    id SERIAL PRIMARY KEY,
    dataset_version VARCHAR(20) NOT NULL UNIQUE,
    source_file_name VARCHAR(255) NOT NULL,
    source_file_hash VARCHAR(64) NOT NULL,  -- SHA-256
    
    -- M5: Migration tracking
    schema_version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    schema_checksum VARCHAR(64),  -- SHA-256 of schema file
    migration_applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- M6: Dataset freeze
    is_frozen BOOLEAN DEFAULT FALSE,
    approved_at TIMESTAMP,
    approved_by VARCHAR(100),
    
    -- Data quality metrics
    total_rows_processed INTEGER,
    total_rows_accepted INTEGER,
    total_rows_rejected INTEGER,
    
    -- Temporal coverage
    date_range_start DATE,
    date_range_end DATE,
    
    -- Processing metadata
    processing_time_seconds NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE stp_dataset_metadata IS 'Dataset versioning, provenance, and freeze status (M5, M6)';
COMMENT ON COLUMN stp_dataset_metadata.dataset_version IS 'Semantic version (e.g., v1.0.0)';
COMMENT ON COLUMN stp_dataset_metadata.source_file_hash IS 'SHA-256 hash of source Excel file';
COMMENT ON COLUMN stp_dataset_metadata.schema_version IS 'M5: Database schema version';
COMMENT ON COLUMN stp_dataset_metadata.schema_checksum IS 'M5: SHA-256 of schema SQL file';
COMMENT ON COLUMN stp_dataset_metadata.is_frozen IS 'M6: If TRUE, dataset is immutable';
COMMENT ON COLUMN stp_dataset_metadata.approved_by IS 'M6: User who approved/froze dataset';

CREATE INDEX idx_stp_metadata_version ON stp_dataset_metadata(dataset_version);
CREATE INDEX idx_stp_metadata_frozen ON stp_dataset_metadata(is_frozen);

-- =====================================================
-- TABLE 5: Governance Declarations (M1-M10, O1-O2)
-- =====================================================
-- Purpose: Store all governance policies and declarations

CREATE TABLE IF NOT EXISTS stp_governance_declarations (
    id SERIAL PRIMARY KEY,
    declaration_type VARCHAR(100) NOT NULL,
    declaration_text TEXT NOT NULL,
    dataset_version VARCHAR(20) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE stp_governance_declarations IS 'Ethics, methodology, and governance declarations (M1-M10, O1-O2)';
COMMENT ON COLUMN stp_governance_declarations.declaration_type IS 'Type: privacy, episode_governance, ast_heterogeneity, etc.';

CREATE INDEX idx_stp_governance_type ON stp_governance_declarations(declaration_type);
CREATE INDEX idx_stp_governance_version ON stp_governance_declarations(dataset_version);

-- =====================================================
-- TABLE 6: Column Provenance Registry (M7)
-- =====================================================
-- Purpose: Track raw vs derived vs normalized columns

CREATE TABLE IF NOT EXISTS stp_column_provenance (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    column_name VARCHAR(100) NOT NULL,
    origin VARCHAR(50) NOT NULL,  -- 'raw', 'derived', 'normalized', 'metadata'
    description TEXT,
    transformation_logic TEXT,  -- How it was created
    introduced_in_stage INTEGER DEFAULT 1,
    dataset_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(table_name, column_name, dataset_version)
);

COMMENT ON TABLE stp_column_provenance IS 'M7: Column-level lineage tracking (raw vs derived vs normalized)';
COMMENT ON COLUMN stp_column_provenance.origin IS 'Source type: raw, derived, normalized, or metadata';
COMMENT ON COLUMN stp_column_provenance.transformation_logic IS 'How this column was created/transformed';

CREATE INDEX idx_stp_provenance_table ON stp_column_provenance(table_name);
CREATE INDEX idx_stp_provenance_origin ON stp_column_provenance(origin);

-- =====================================================
-- TABLE 7: Raw Wide Format (Validated)
-- =====================================================
-- Purpose: Validated wide-format AST data (one row per isolate)

CREATE TABLE IF NOT EXISTS stp_raw_wide (
    id BIGSERIAL PRIMARY KEY,
    isolate_id VARCHAR(100) NOT NULL,  -- Lab_No as isolate identifier (non-PII)
    sample_date DATE NOT NULL,
    organism VARCHAR(200) NOT NULL,
    ward VARCHAR(100) NOT NULL,
    sample_type VARCHAR(100),
    
    -- Wide antibiotic columns stored as JSONB
    -- Format: {"Penicillin": "S", "Vancomycin": "R", "Linezolid": "NA", ...}
    antibiotic_results JSONB NOT NULL,
    
    -- Metadata
    dataset_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (organism) REFERENCES stp_organism_taxonomy(canonical_name),
    FOREIGN KEY (ward) REFERENCES stp_ward_taxonomy(ward_name),
    
    -- Uniqueness per version
    UNIQUE(isolate_id, dataset_version)
);

COMMENT ON TABLE stp_raw_wide IS 'Validated wide-format AST data (one row per isolate)';
COMMENT ON COLUMN stp_raw_wide.isolate_id IS 'Lab_No as isolate identifier (M1: no deduplication)';
COMMENT ON COLUMN stp_raw_wide.antibiotic_results IS 'JSONB: {"antibiotic": "S|I|R|NA", ...}';

CREATE INDEX idx_stp_raw_date ON stp_raw_wide(sample_date);
CREATE INDEX idx_stp_raw_organism ON stp_raw_wide(organism);
CREATE INDEX idx_stp_raw_ward ON stp_raw_wide(ward);
CREATE INDEX idx_stp_raw_version ON stp_raw_wide(dataset_version);
CREATE INDEX idx_stp_raw_isolate ON stp_raw_wide(isolate_id);

-- GIN index for JSONB queries
CREATE INDEX idx_stp_raw_antibiotics_gin ON stp_raw_wide USING GIN (antibiotic_results);

-- =====================================================
-- TABLE 8: Canonical Long Format (MAIN OUTPUT)
-- =====================================================
-- Purpose: Analysis-ready long format (one row per AST test)
-- This is the PRIMARY output of Stage 1

CREATE TABLE IF NOT EXISTS stp_canonical_long (
    id BIGSERIAL PRIMARY KEY,
    isolate_id VARCHAR(100) NOT NULL,
    sample_date DATE NOT NULL,
    organism VARCHAR(200) NOT NULL,
    ward VARCHAR(100) NOT NULL,
    sample_type VARCHAR(100),
    antibiotic VARCHAR(100) NOT NULL,
    ast_result VARCHAR(2) NOT NULL CHECK (ast_result IN ('S', 'I', 'R', 'NA')),
    
    -- Metadata
    dataset_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (organism) REFERENCES stp_organism_taxonomy(canonical_name),
    FOREIGN KEY (ward) REFERENCES stp_ward_taxonomy(ward_name)
);

COMMENT ON TABLE stp_canonical_long IS 'MAIN OUTPUT: Analysis-ready long format (one row per AST test)';
COMMENT ON COLUMN stp_canonical_long.isolate_id IS 'Lab_No as isolate identifier';
COMMENT ON COLUMN stp_canonical_long.ast_result IS 'S=Susceptible, I=Intermediate, R=Resistant, NA=Not Tested (M2)';

-- Critical indexes for performance
CREATE INDEX idx_stp_long_date ON stp_canonical_long(sample_date);
CREATE INDEX idx_stp_long_organism ON stp_canonical_long(organism);
CREATE INDEX idx_stp_long_ward ON stp_canonical_long(ward);
CREATE INDEX idx_stp_long_antibiotic ON stp_canonical_long(antibiotic);
CREATE INDEX idx_stp_long_ast_result ON stp_canonical_long(ast_result);
CREATE INDEX idx_stp_long_version ON stp_canonical_long(dataset_version);

-- Composite index for common queries
CREATE INDEX idx_stp_long_combo ON stp_canonical_long(organism, antibiotic, ward, sample_date);

-- =====================================================
-- TABLE 9: Data Quality Log (Audit Trail)
-- =====================================================
-- Purpose: Complete audit trail of all rejections

CREATE TABLE IF NOT EXISTS stp_data_quality_log (
    id BIGSERIAL PRIMARY KEY,
    row_index INTEGER,
    rejection_reason VARCHAR(100) NOT NULL,
    details JSONB,  -- Detailed context
    organism_provided VARCHAR(200),
    ward_provided VARCHAR(100),
    sample_date_provided DATE,
    dataset_version VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE stp_data_quality_log IS 'Audit trail of all data rejections (publication defense)';
COMMENT ON COLUMN stp_data_quality_log.rejection_reason IS 'Standardized reason code';
COMMENT ON COLUMN stp_data_quality_log.details IS 'JSONB with full context';

CREATE INDEX idx_stp_quality_reason ON stp_data_quality_log(rejection_reason);
CREATE INDEX idx_stp_quality_version ON stp_data_quality_log(dataset_version);
CREATE INDEX idx_stp_quality_date ON stp_data_quality_log(created_at);

-- =====================================================
-- VIEW: Stage 1 Read-Only (M10 Stage Boundary)
-- =====================================================
-- Purpose: Provide read-only access to Stage 2+

CREATE OR REPLACE VIEW stp_stage1_readonly AS
SELECT 
    id,
    isolate_id,
    sample_date,
    organism,
    ward,
    sample_type,
    antibiotic,
    ast_result,
    dataset_version
FROM stp_canonical_long
WHERE dataset_version IN (
    SELECT dataset_version 
    FROM stp_dataset_metadata 
    WHERE is_frozen = TRUE
);

COMMENT ON VIEW stp_stage1_readonly IS 'M10: Read-only view for Stage 2+ (only frozen datasets)';

-- =====================================================
-- HELPER FUNCTIONS
-- =====================================================

-- Function: Get latest dataset version
CREATE OR REPLACE FUNCTION get_latest_stp_dataset_version()
RETURNS TABLE(
    dataset_version VARCHAR(20),
    is_frozen BOOLEAN,
    total_isolates BIGINT,
    created_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.dataset_version,
        m.is_frozen,
        COUNT(l.id) as total_isolates,
        m.created_at
    FROM stp_dataset_metadata m
    LEFT JOIN stp_canonical_long l ON l.dataset_version = m.dataset_version
    GROUP BY m.dataset_version, m.is_frozen, m.created_at
    ORDER BY m.created_at DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function: Check if organism is allowed
CREATE OR REPLACE FUNCTION is_stp_organism_allowed(organism_name VARCHAR(200))
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM stp_organism_taxonomy
        WHERE canonical_name = organism_name
        AND is_active = TRUE
    );
END;
$$ LANGUAGE plpgsql;

-- Function: Normalize organism name
CREATE OR REPLACE FUNCTION normalize_stp_organism(input_name VARCHAR(200))
RETURNS VARCHAR(200) AS $$
DECLARE
    canonical VARCHAR(200);
BEGIN
    -- Direct match
    SELECT canonical_name INTO canonical
    FROM stp_organism_taxonomy
    WHERE canonical_name = input_name
    AND is_active = TRUE;
    
    IF canonical IS NOT NULL THEN
        RETURN canonical;
    END IF;
    
    -- Synonym match
    SELECT canonical_name INTO canonical
    FROM stp_organism_taxonomy
    WHERE input_name = ANY(synonyms)
    AND is_active = TRUE;
    
    RETURN canonical;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- SUMMARY VIEWS (For Governance Reports)
-- =====================================================

-- Organism distribution
CREATE OR REPLACE VIEW stp_organism_distribution AS
SELECT 
    organism,
    dataset_version,
    COUNT(*) as isolate_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY dataset_version), 2) as percentage
FROM stp_canonical_long
GROUP BY organism, dataset_version
ORDER BY dataset_version, isolate_count DESC;

-- Ward distribution
CREATE OR REPLACE VIEW stp_ward_distribution AS
SELECT 
    ward,
    dataset_version,
    COUNT(DISTINCT isolate_id) as isolate_count,
    ROUND(COUNT(DISTINCT isolate_id) * 100.0 / SUM(COUNT(DISTINCT isolate_id)) OVER (PARTITION BY dataset_version), 2) as percentage
FROM stp_canonical_long
GROUP BY ward, dataset_version
ORDER BY dataset_version, isolate_count DESC;

-- Antibiotic testing frequency
CREATE OR REPLACE VIEW stp_antibiotic_testing_frequency AS
SELECT 
    antibiotic,
    dataset_version,
    COUNT(*) as test_count,
    COUNT(DISTINCT isolate_id) as isolates_tested,
    ROUND(COUNT(DISTINCT isolate_id) * 100.0 / (
        SELECT COUNT(DISTINCT isolate_id) 
        FROM stp_canonical_long c2 
        WHERE c2.dataset_version = c1.dataset_version
    ), 2) as coverage_percent
FROM stp_canonical_long c1
GROUP BY antibiotic, dataset_version
ORDER BY dataset_version, test_count DESC;

-- =====================================================
-- SCHEMA METADATA
-- =====================================================

-- Store schema checksum for M5
INSERT INTO stp_dataset_metadata (
    dataset_version,
    source_file_name,
    source_file_hash,
    schema_version,
    schema_checksum,
    migration_applied_at
) VALUES (
    'v0.0.0-schema',
    'SCHEMA_ONLY',
    'SCHEMA_ONLY',
    '1.0.0',
    'WILL_BE_COMPUTED',  -- Will be updated by stp_dataset_hasher.py
    CURRENT_TIMESTAMP
) ON CONFLICT (dataset_version) DO NOTHING;

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

DO $$ 
BEGIN 
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'STP Stage 1 Schema Created Successfully';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Tables: 9 core tables + 1 view';
    RAISE NOTICE 'Governance: M1-M10 components integrated';
    RAISE NOTICE 'Version: 1.0.0';
    RAISE NOTICE 'Status: Ready for data ingestion';
    RAISE NOTICE '==============================================';
END $$;
