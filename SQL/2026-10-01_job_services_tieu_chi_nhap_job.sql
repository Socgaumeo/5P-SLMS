-- Áp file "THÔNG TIN NHẬP JOB" (Khánh chốt 30/09–01/10/2026)
-- Thêm 8 cột cho job_services. Chỉ THÊM, không sửa/xoá dữ liệu cũ. Không bóc ngược.
BEGIN;
ALTER TABLE job_services
  ADD COLUMN IF NOT EXISTS incoterm      VARCHAR(10),   -- TERM: EXW/FOB/CIF/CIP/DAP/DDP...
  ADD COLUMN IF NOT EXISTS booking_no    VARCHAR(50),   -- sea: số booking; air: số MAWB (= booking)
  ADD COLUMN IF NOT EXISTS mbl_no        VARCHAR(50),   -- sea: số MBL (bl_awb_no giữ HBL/vận đơn)
  ADD COLUMN IF NOT EXISTS carrier       VARCHAR(120),  -- hãng tàu / hãng bay (khác vendor = bên 5P trả tiền)
  ADD COLUMN IF NOT EXISTS vessel_flight VARCHAR(120),  -- tên tàu/chuyến (sea) hoặc số chuyến bay (air)
  ADD COLUMN IF NOT EXISTS phan_luong    VARCHAR(10),   -- tờ khai: XANH / VANG / DO
  ADD COLUMN IF NOT EXISTS atd           DATE,          -- ngày đi THỰC TẾ (ETD dự kiến ở jobs.etd)
  ADD COLUMN IF NOT EXISTS delivery_date DATE;          -- ngày giao hàng (nếu có)
ALTER TABLE job_services DROP CONSTRAINT IF EXISTS job_services_phan_luong_chk;
ALTER TABLE job_services ADD CONSTRAINT job_services_phan_luong_chk
  CHECK (phan_luong IS NULL OR phan_luong IN ('XANH','VANG','DO'));
CREATE INDEX IF NOT EXISTS idx_job_services_booking_no ON job_services (booking_no) WHERE booking_no IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_job_services_mbl_no     ON job_services (mbl_no)     WHERE mbl_no IS NOT NULL;
COMMIT;
