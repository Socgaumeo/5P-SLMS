-- ============================================================
-- AUTO-DERIVE JOB STATUS từ job_services (2026-07-15)
-- Chỉ đạo BeaR: bỏ CONFIRMED; job status tự suy từ nội dung service.
-- Luồng: DRAFT (chưa service) → PENDING (có service, chưa gán) →
--        IN_PROGRESS (service có xe/người/vendor) → COMPLETED / CANCELLED
-- Mốc IN_PROGRESS = service có 1 trong: vehicle_id / driver_id /
--        employee_id / vendor_id / vendor_text_input (khác rỗng)
-- ============================================================

-- BƯỚC 1 — IN_PROGRESS đã tồn tại trong master_statuses (name_vi='Đang thực hiện')
-- Không cần INSERT thêm.

-- BƯỚC 2 — Hàm suy job status từ các service của nó
CREATE OR REPLACE FUNCTION derive_job_status(p_job_id INT)
RETURNS TEXT AS $$
DECLARE
  cur_status  TEXT;
  svc_count   INT;
  assigned    INT;
  done_count  INT;
BEGIN
  SELECT status_code INTO cur_status FROM jobs WHERE job_id = p_job_id;

  -- Giữ nguyên nếu job đã COMPLETED / CANCELLED (trạng thái cuối, không auto-đổi)
  IF cur_status IN ('COMPLETED','CANCELLED') THEN
    RETURN cur_status;
  END IF;

  SELECT COUNT(*) INTO svc_count FROM job_services WHERE job_id = p_job_id;
  IF svc_count = 0 THEN
    RETURN 'DRAFT';
  END IF;

  -- Đếm service đã gán xe/người/vendor
  SELECT COUNT(*) INTO assigned FROM job_services
   WHERE job_id = p_job_id
     AND ( vehicle_id IS NOT NULL
        OR driver_id IS NOT NULL
        OR employee_id IS NOT NULL
        OR vendor_id IS NOT NULL
        OR (vendor_text_input IS NOT NULL AND btrim(vendor_text_input) <> '') );

  IF assigned > 0 THEN
    RETURN 'IN_PROGRESS';
  END IF;

  RETURN 'PENDING';
END;
$$ LANGUAGE plpgsql;

-- BƯỚC 3 — Trigger trên job_services: mỗi khi thêm/sửa/xóa service → cập nhật status job
CREATE OR REPLACE FUNCTION sync_job_status_from_service()
RETURNS TRIGGER AS $$
DECLARE
  tgt_job INT;
  new_st  TEXT;
BEGIN
  tgt_job := COALESCE(NEW.job_id, OLD.job_id);
  IF tgt_job IS NULL THEN
    RETURN COALESCE(NEW, OLD);
  END IF;

  new_st := derive_job_status(tgt_job);

  UPDATE jobs SET status_code = new_st
   WHERE job_id = tgt_job
     AND status_code IS DISTINCT FROM new_st
     AND status_code NOT IN ('COMPLETED','CANCELLED');

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_job_status ON job_services;
CREATE TRIGGER trg_sync_job_status
  AFTER INSERT OR UPDATE OF vehicle_id, driver_id, employee_id, vendor_id, vendor_text_input, job_id
      OR DELETE ON job_services
  FOR EACH ROW EXECUTE FUNCTION sync_job_status_from_service();
