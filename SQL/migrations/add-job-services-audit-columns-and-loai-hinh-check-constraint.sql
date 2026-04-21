-- Phase 6+ migration: close gaps in job creation paths
-- 1. Add created_by / updated_by to job_services for full audit trail
-- 2. CHECK constraint: customs services MUST have non-empty loai_hinh
--
-- The CHECK uses NOT VALID so the 164 legacy CUS_* rows that currently lack
-- loai_hinh do NOT fail the migration. New inserts / updates still enforced.
-- Run `ALTER TABLE ... VALIDATE CONSTRAINT ...` later once legacy backfill done.

BEGIN;

-- ============================================================================
-- 1. Audit columns on job_services
-- ============================================================================
ALTER TABLE job_services
    ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(user_id),
    ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(user_id);

CREATE INDEX IF NOT EXISTS idx_job_services_created_by ON job_services(created_by);


-- ============================================================================
-- 2. CHECK constraint: customs services require loai_hinh
-- ============================================================================
-- Matches the same service-type set as the Python validator in
-- app.core.vietnamese-customs-declaration-codes-and-validator:
--   - CUS (exact)
--   - CUS_IMPORT* (prefix)
--   - CUS_EXPORT* (prefix)
-- CUS_CO (Certificate of Origin) is intentionally NOT customs — no loai_hinh needed.
ALTER TABLE job_services
    DROP CONSTRAINT IF EXISTS customs_services_require_loai_hinh;

ALTER TABLE job_services
    ADD CONSTRAINT customs_services_require_loai_hinh
    CHECK (
        -- Non-customs services: always pass
        (service_type_code IS NULL)
        OR (service_type_code NOT LIKE 'CUS_IMPORT%'
            AND service_type_code NOT LIKE 'CUS_EXPORT%'
            AND service_type_code <> 'CUS')
        -- Customs services: loai_hinh must be non-empty
        OR (loai_hinh IS NOT NULL AND btrim(loai_hinh) <> '')
    )
    NOT VALID;

-- Sanity check: list how many existing rows would fail if we were to VALIDATE now.
-- (This is a no-op SELECT — just informational; actual VALIDATE is deferred.)
DO $$
DECLARE
    legacy_violations INT;
BEGIN
    SELECT COUNT(*) INTO legacy_violations
    FROM job_services
    WHERE (service_type_code LIKE 'CUS_IMPORT%'
           OR service_type_code LIKE 'CUS_EXPORT%'
           OR service_type_code = 'CUS')
      AND (loai_hinh IS NULL OR btrim(loai_hinh) = '');
    RAISE NOTICE 'Legacy rows needing loai_hinh backfill: %', legacy_violations;
END $$;

COMMIT;

-- After legacy backfill is complete, run:
--   ALTER TABLE job_services VALIDATE CONSTRAINT customs_services_require_loai_hinh;
