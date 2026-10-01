BEGIN;
DROP INDEX IF EXISTS idx_job_services_booking_no;
DROP INDEX IF EXISTS idx_job_services_mbl_no;
ALTER TABLE job_services DROP CONSTRAINT IF EXISTS job_services_phan_luong_chk;
ALTER TABLE job_services DROP COLUMN IF EXISTS incoterm, DROP COLUMN IF EXISTS booking_no,
  DROP COLUMN IF EXISTS mbl_no, DROP COLUMN IF EXISTS carrier, DROP COLUMN IF EXISTS vessel_flight,
  DROP COLUMN IF EXISTS phan_luong, DROP COLUMN IF EXISTS atd, DROP COLUMN IF EXISTS delivery_date;
COMMIT;
