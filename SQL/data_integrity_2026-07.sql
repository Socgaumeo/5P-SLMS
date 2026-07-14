-- =====================================================================
-- DATA INTEGRITY MIGRATION — 5P SLMS  (v2, theo chỉ đạo Khánh 14/07)
-- 1. Gộp HẾT trucking con (SHORT/LONG/CONT/DOM) về 1 code duy nhất: TRUCKING
--    → đặc điểm (nội thành/liên tỉnh/cont/nội địa) thể hiện trong chi tiết job.
-- 2. Thiếu giá: CẢNH BÁO ở các bước, nhưng CHẶN CỨNG khi COMPLETED.
-- 3. FK service_type → master + chống job mồ côi.
-- Chạy trong 1 transaction. DEFERRABLE trigger để tạo job+service+cost cùng lúc OK.
-- =====================================================================
BEGIN;

-- ---------------------------------------------------------------------
-- BƯỚC 1 — Chuẩn hoá master: tạo/kích hoạt code 'TRUCKING', tắt các con
-- ---------------------------------------------------------------------
INSERT INTO master_service_types (service_code, name_vi, sort_order, is_active, category)
VALUES ('TRUCKING', 'Vận tải đường bộ', 1, true, 'TRUCKING')
ON CONFLICT (service_code) DO UPDATE SET is_active = true, name_vi = EXCLUDED.name_vi;

UPDATE master_service_types
SET is_active = false
WHERE service_code IN ('TRUCKING_SHORT','TRUCKING_LONG','TRUCKING_CONT','TRUCKING_DOM')
  AND service_code <> 'TRUCKING';

-- ---------------------------------------------------------------------
-- BƯỚC 2 — Gộp data: mọi code trucking con → 'TRUCKING'
-- ---------------------------------------------------------------------
UPDATE job_services
SET service_type_code = 'TRUCKING'
WHERE service_type_code IN ('TRUCKING_SHORT','TRUCKING_LONG','TRUCKING_CONT','TRUCKING_DOM');

UPDATE vendor_rates
SET service_type_code = 'TRUCKING'
WHERE service_type_code IN ('TRUCKING_SHORT','TRUCKING_LONG','TRUCKING_CONT','TRUCKING_DOM');

-- ---------------------------------------------------------------------
-- BƯỚC 3 — Kiểm tra không còn code lạc (phải rỗng thì FK mới thêm được)
-- ---------------------------------------------------------------------
-- (SELECT chỉ để log — nếu có row trả về, transaction vẫn tiếp; kiểm bằng mắt trong output)

-- ---------------------------------------------------------------------
-- BƯỚC 4 — FK service_type_code → master_service_types
-- ---------------------------------------------------------------------
ALTER TABLE job_services
  DROP CONSTRAINT IF EXISTS fk_job_services_service_type;
ALTER TABLE job_services
  ADD CONSTRAINT fk_job_services_service_type
  FOREIGN KEY (service_type_code)
  REFERENCES master_service_types(service_code)
  ON UPDATE CASCADE;

-- ---------------------------------------------------------------------
-- BƯỚC 5 — job_id NOT NULL (chống service mồ côi)
-- ---------------------------------------------------------------------
ALTER TABLE job_services ALTER COLUMN job_id SET NOT NULL;

-- ---------------------------------------------------------------------
-- BƯỚC 6 — Trigger chống JOB MỒ CÔI: không rời DRAFT khi chưa có service
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION check_job_has_service()
RETURNS TRIGGER AS $$
DECLARE svc_count int;
BEGIN
  IF NEW.status_code IS NULL OR NEW.status_code = 'DRAFT' THEN
    RETURN NEW;
  END IF;
  SELECT count(*) INTO svc_count FROM job_services WHERE job_id = NEW.job_id;
  IF svc_count = 0 THEN
    RAISE EXCEPTION 'Job % (status %) chưa có service nào — không được rời DRAFT.', NEW.job_id, NEW.status_code;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_job_has_service ON jobs;
CREATE CONSTRAINT TRIGGER trg_job_has_service
  AFTER INSERT OR UPDATE OF status_code ON jobs
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION check_job_has_service();

-- ---------------------------------------------------------------------
-- BƯỚC 7 — Trigger GIÁ: cảnh báo khi thiếu, CHẶN CỨNG khi COMPLETED
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION check_job_has_price()
RETURNS TRIGGER AS $$
DECLARE cost_rows int;
BEGIN
  SELECT count(*) INTO cost_rows
  FROM job_costs
  WHERE job_id = NEW.job_id
    AND (COALESCE(buying_amount,0) > 0 OR COALESCE(selling_amount,0) > 0);

  IF cost_rows = 0 THEN
    IF NEW.status_code = 'COMPLETED' THEN
      RAISE EXCEPTION 'Job % không được COMPLETED khi chưa có giá mua/bán (job_costs trống). Điền giá trước.', NEW.job_id;
    ELSIF NEW.status_code IN ('CONFIRMED','DISPATCHED') THEN
      RAISE WARNING 'Job % (status %) chưa có giá mua/bán — nhắc điền giá.', NEW.job_id, NEW.status_code;
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_job_has_price ON jobs;
CREATE CONSTRAINT TRIGGER trg_job_has_price
  AFTER INSERT OR UPDATE OF status_code ON jobs
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION check_job_has_price();

COMMIT;

-- ROLLBACK gỡ (nếu cần):
-- ALTER TABLE job_services DROP CONSTRAINT fk_job_services_service_type;
-- ALTER TABLE job_services ALTER COLUMN job_id DROP NOT NULL;
-- DROP TRIGGER IF EXISTS trg_job_has_service ON jobs; DROP FUNCTION check_job_has_service();
-- DROP TRIGGER IF EXISTS trg_job_has_price ON jobs;   DROP FUNCTION check_job_has_price();
