-- =====================================================
-- STP Stage 1: Ward Taxonomy Initialization
-- =====================================================
-- Purpose: Initialize stp_ward_taxonomy from existing master_definitions
-- Reuses existing ward standardization for consistency

-- Insert wards from master_definitions
INSERT INTO stp_ward_taxonomy (ward_name, is_icu, specialty_group, is_active)
SELECT 
    value as ward_name,
    CASE 
        WHEN LOWER(value) LIKE '%icu%' THEN TRUE
        ELSE FALSE
    END as is_icu,
    CASE 
        WHEN LOWER(value) LIKE '%icu%' THEN 'Critical Care'
        WHEN LOWER(value) LIKE '%opd%' OR LOWER(value) LIKE '%o/c%' THEN 'Outpatient'
        WHEN LOWER(value) LIKE '%a&e%' OR LOWER(value) LIKE '%emergency%' THEN 'Emergency'
        WHEN LOWER(value) LIKE '%ward%' THEN 'Inpatient'
        ELSE 'Other'
    END as specialty_group,
    is_active
FROM master_definitions
WHERE category = 'WARD'
ON CONFLICT (ward_name) DO UPDATE SET
    is_icu = EXCLUDED.is_icu,
    specialty_group = EXCLUDED.specialty_group,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

-- Log results
DO $$ 
DECLARE
    ward_count INTEGER;
BEGIN 
    SELECT COUNT(*) INTO ward_count FROM stp_ward_taxonomy;
    RAISE NOTICE 'Ward taxonomy initialized: % wards loaded', ward_count;
END $$;
