-- =====================================================
-- STP Stage 1: Supabase Row-Level Security Policies
-- =====================================================
-- Purpose: M8 - Implement access control policies
-- 
-- Access Policy:
--   - Raw tables: Authenticated users only
--   - Metadata/governance: Public read
--   - Write operations: Service role only
-- =====================================================

-- Enable Row Level Security on sensitive tables
ALTER TABLE stp_raw_wide ENABLE ROW LEVEL SECURITY;
ALTER TABLE stp_canonical_long ENABLE ROW LEVEL SECURITY;
ALTER TABLE stp_data_quality_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE stp_dataset_metadata ENABLE ROW LEVEL SECURITY;
ALTER TABLE stp_governance_declarations ENABLE ROW LEVEL SECURITY;
ALTER TABLE stp_column_provenance ENABLE ROW LEVEL SECURITY;

-- =====================================================
-- POLICIES: Raw Data Tables (Authenticated Access)
-- =====================================================

-- Policy: Authenticated users can read stp_raw_wide
CREATE POLICY "stp_raw_wide_read_authenticated"
ON stp_raw_wide FOR SELECT
USING (auth.role() = 'authenticated');

-- Policy: Service role can write stp_raw_wide
CREATE POLICY "stp_raw_wide_write_service"
ON stp_raw_wide FOR INSERT
USING (auth.role() = 'service_role');

-- Policy: Authenticated users can read stp_canonical_long
CREATE POLICY "stp_canonical_long_read_authenticated"
ON stp_canonical_long FOR SELECT
USING (auth.role() = 'authenticated');

-- Policy: Service role can write stp_canonical_long
CREATE POLICY "stp_canonical_long_write_service"
ON stp_canonical_long FOR INSERT
USING (auth.role() = 'service_role');

-- Policy: Authenticated users can read quality log
CREATE POLICY "stp_quality_log_read_authenticated"
ON stp_data_quality_log FOR SELECT
USING (auth.role() = 'authenticated');

-- Policy: Service role can write quality log
CREATE POLICY "stp_quality_log_write_service"
ON stp_data_quality_log FOR INSERT
USING (auth.role() = 'service_role');

-- =====================================================
-- POLICIES: Metadata Tables (Public Read)
-- =====================================================

-- Policy: Public can read metadata
CREATE POLICY "stp_metadata_read_public"
ON stp_dataset_metadata FOR SELECT
USING (true);

-- Policy: Service role can write metadata
CREATE POLICY "stp_metadata_write_service"
ON stp_dataset_metadata FOR ALL
USING (auth.role() = 'service_role');

-- Policy: Public can read governance declarations
CREATE POLICY "stp_governance_read_public"
ON stp_governance_declarations FOR SELECT
USING (true);

-- Policy: Service role can write governance
CREATE POLICY "stp_governance_write_service"
ON stp_governance_declarations FOR ALL
USING (auth.role() = 'service_role');

-- Policy: Public can read column provenance (M7)
CREATE POLICY "stp_provenance_read_public"
ON stp_column_provenance FOR SELECT
USING (true);

-- Policy: Service role can write provenance
CREATE POLICY "stp_provenance_write_service"
ON stp_column_provenance FOR ALL
USING (auth.role() = 'service_role');

-- =====================================================
-- COMPLETION MESSAGE
-- =====================================================

DO $$ 
BEGIN 
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'STP RLS Policies Created (M8)';
    RAISE NOTICE '==============================================';
    RAISE NOTICE 'Raw data: Authenticated access only';
    RAISE NOTICE 'Metadata/Governance: Public read';
    RAISE NOTICE 'Write operations: Service role only';
    RAISE NOTICE '==============================================';
END $$;
