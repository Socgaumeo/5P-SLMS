-- =====================================================================
-- DATA INTEGRITY MIGRATION — 5P SLMS
-- Ngày: 2026-07-14 · Soạn: Sen
-- MỤC ĐÍCH: đẩy các invariant nghiệp vụ từ tầng AI/skill (mềm) xuống DB (cứng)
-- ĐỌC KỸ TRƯỚC KHI CHẠY. Chạy trên Supabase SQL Editor, TỪNG BƯỚC, có kiểm tra.
-- =====================================================================

-- ---------------------------------------------------------------------
-- BƯỚC 0 — DỌN DATA CŨ (bắt buộc trước khi thêm ràng buộc)
-- ---------------------------------------------------------------------

-- 0.1 · 35 row job_services đang dùng code 'TRUCKING' (không có trong master)
--      → đổi sang 'TRUCKING_DOM'. (Lỗi tồn dư từ incident 02/07.)
-- KIỂM TRA TRƯỚC:
SELECT service_type_code, count(*)
FROM job_services
WHERE service_type_code = 'TRUCKING'
GROUP BY service_type_code;

-- SỬA (bỏ comment để chạy):
-- UPDATE job_services
-- SET service_type_code = 'TRUCKING_DOM', updated_at = now()
-- WHERE service_type_code = 'TRUCKING';

-- 0.2 · Kiểm tra còn code nào KHÔNG khớp master không (phải = 0 mới thêm FK được)
SELECT js.service_type_code, count(*)
FROM job_services js
LEFT JOIN master_service_types m ON m.service_code = js.service_type_code
WHERE js.service_type_code IS NOT NULL AND m.service_code IS NULL
GROUP BY js.service_type_code;

-- 0.3 · Kiểm tra job mồ côi (không có service). Hiện tại = 0. Nếu >0 phải xử lý thủ công.
SELECT j.job_id, j.job_no, j.status_code
FROM jobs j
LEFT JOIN job_services js ON js.job_id = j.job_id
WHERE js.job_id IS NULL;


-- ---------------------------------------------------------------------
-- RÀNG BUỘC 1 — service_type_code phải tồn tại trong master (FK)
-- Chặn: gõ sai mã như 'TRUCKING' → DB từ chối.
-- ---------------------------------------------------------------------
-- Chạy SAU KHI bước 0.2 trả về rỗng.
ALTER TABLE job_services
  ADD CONSTRAINT fk_job_services_service_type
  FOREIGN KEY (service_type_code)
  REFERENCES master_service_types(service_code)
  ON UPDATE CASCADE;   -- đổi tên code ở master tự lan sang job_services


-- ---------------------------------------------------------------------
-- RÀNG BUỘC 2 — job_services.job_id bắt buộc + xóa job thì xóa service (FK cascade)
-- Chặn: service trỏ tới job không tồn tại; và dọn sạch khi hủy job.
-- ---------------------------------------------------------------------
-- (Chỉ thêm nếu chưa có FK. Kiểm tra: \d job_services)
ALTER TABLE job_services
  ALTER COLUMN job_id SET NOT NULL;

-- Nếu chưa có FK job_id → jobs, thêm:
-- ALTER TABLE job_services
--   ADD CONSTRAINT fk_job_services_job
--   FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE;


-- ---------------------------------------------------------------------
-- RÀNG BUỘC 3 — CHẶN JOB MỒ CÔI: job không được ở trạng thái ≥ CONFIRMED
--               nếu chưa có service nào. (Deferred trigger — kiểm ở cuối transaction)
-- Lý do dùng trigger thay vì FK: 1 job có thể có nhiều service, không FK ngược được.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION check_job_has_service()
RETURNS TRIGGER AS $$
DECLARE
  svc_count int;
  st text;
BEGIN
  -- chỉ kiểm khi job đã qua DRAFT
  SELECT status_code INTO st FROM jobs WHERE job_id = NEW.job_id;
  IF st IS NULL OR st = 'DRAFT' THEN
    RETURN NEW;
  END IF;
  SELECT count(*) INTO svc_count FROM job_services WHERE job_id = NEW.job_id;
  IF svc_count = 0 THEN
    RAISE EXCEPTION 'Job % (status %) không có service nào — không được rời trạng thái DRAFT khi chưa có dịch vụ.', NEW.job_id, st;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger AFTER trên jobs khi đổi status khác DRAFT (DEFERRABLE để cho phép insert job+service cùng transaction)
DROP TRIGGER IF EXISTS trg_job_has_service ON jobs;
CREATE CONSTRAINT TRIGGER trg_job_has_service
  AFTER INSERT OR UPDATE OF status_code ON jobs
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW
  EXECUTE FUNCTION check_job_has_service();


-- ---------------------------------------------------------------------
-- RÀNG BUỘC 4 — CHẶN THIẾU GIÁ: job không được sang CONFIRMED/DISPATCHED/COMPLETED
--               nếu chưa có job_costs (giá mua/bán) HOẶC total_revenue/total_cost = 0.
-- Mức độ: cảnh báo cứng (EXCEPTION). Có thể đổi thành WARNING nếu muốn mềm hơn.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION check_job_has_price()
RETURNS TRIGGER AS $$
DECLARE
  cost_rows int;
BEGIN
  -- chỉ chặn khi job chuyển sang các trạng thái "đã chốt"
  IF NEW.status_code NOT IN ('CONFIRMED','DISPATCHED','COMPLETED') THEN
    RETURN NEW;
  END IF;
  SELECT count(*) INTO cost_rows
  FROM job_costs
  WHERE job_id = NEW.job_id
    AND (COALESCE(buying_amount,0) > 0 OR COALESCE(selling_amount,0) > 0);
  IF cost_rows = 0 THEN
    RAISE EXCEPTION 'Job % chuyển sang % nhưng chưa có giá mua/bán (job_costs trống hoặc = 0). Điền giá trước khi chốt.', NEW.job_id, NEW.status_code;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_job_has_price ON jobs;
CREATE CONSTRAINT TRIGGER trg_job_has_price
  AFTER INSERT OR UPDATE OF status_code ON jobs
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW
  EXECUTE FUNCTION check_job_has_price();


-- ---------------------------------------------------------------------
-- RÀNG BUỘC 5 — status_code chỉ nhận giá trị trong master_statuses (mềm hoá bằng CHECK)
-- ---------------------------------------------------------------------
-- (Tùy chọn — chỉ thêm nếu master_statuses ổn định)
-- ALTER TABLE jobs
--   ADD CONSTRAINT fk_jobs_status FOREIGN KEY (status_code)
--   REFERENCES master_statuses(status_code);


-- ---------------------------------------------------------------------
-- ROLLBACK (nếu cần gỡ)
-- ---------------------------------------------------------------------
-- ALTER TABLE job_services DROP CONSTRAINT fk_job_services_service_type;
-- ALTER TABLE job_services ALTER COLUMN job_id DROP NOT NULL;
-- DROP TRIGGER IF EXISTS trg_job_has_service ON jobs;   DROP FUNCTION check_job_has_service();
-- DROP TRIGGER IF EXISTS trg_job_has_price   ON jobs;   DROP FUNCTION check_job_has_price();

-- =====================================================================
-- GHI CHÚ VẬN HÀNH
-- • Trigger 3,4 dùng CONSTRAINT TRIGGER DEFERRABLE → cho phép tạo job + service + cost
--   trong CÙNG 1 transaction (kiểm tra chỉ chạy khi COMMIT). App phải bọc create-job
--   trong 1 transaction để không bị chặn oan.
-- • Nếu app tạo job DRAFT trước rồi thêm service sau (nhiều bước) → không bị chặn,
--   chỉ bị chặn khi cố chuyển status khỏi DRAFT mà thiếu service/giá.
-- • Muốn nới lỏng: đổi RAISE EXCEPTION thành RAISE WARNING (chỉ log, không chặn).
-- =====================================================================
