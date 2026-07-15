-- ============================================================
-- MODULE KẾ TOÁN CÔNG NỢ AR/AP cho SLMS (2026-07-15)
-- Chỉ đạo BeaR: Full AR + AP (4 bảng). Track tiền ở cấp CHỨNG TỪ.
-- KHÔNG đụng job_costs/jobs hiện có — chỉ THÊM lớp trên.
--   AR (phải thu): gom N job vào 1 invoice, track đã thu.
--   AP (phải trả): gom chi phí vendor/employee vào 1 bill, xuất bảng kê.
-- payment_status: unpaid / partial / paid  (+overdue tính từ due_date)
-- ============================================================

-- ---------- AR: PHẢI THU ----------
CREATE TABLE IF NOT EXISTS ar_invoices (
  invoice_id     SERIAL PRIMARY KEY,
  invoice_no     TEXT UNIQUE,                         -- số hóa đơn (có thể NULL khi nháp)
  customer_id    INT NOT NULL REFERENCES customers(customer_id),
  issue_date     DATE,
  due_date       DATE,
  subtotal       NUMERIC(15,2) DEFAULT 0,             -- tiền trước thuế
  vat_amount     NUMERIC(15,2) DEFAULT 0,
  total          NUMERIC(15,2) DEFAULT 0,             -- subtotal + vat
  currency       TEXT DEFAULT 'VND',
  payment_status TEXT NOT NULL DEFAULT 'unpaid'
                 CHECK (payment_status IN ('unpaid','partial','paid')),
  paid_amount    NUMERIC(15,2) DEFAULT 0,
  paid_date      DATE,
  note           TEXT,
  created_by     INT REFERENCES users(user_id),
  created_at     TIMESTAMPTZ DEFAULT now(),
  updated_at     TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ar_invoice_jobs (
  id               SERIAL PRIMARY KEY,
  invoice_id       INT NOT NULL REFERENCES ar_invoices(invoice_id) ON DELETE CASCADE,
  job_id           INT NOT NULL REFERENCES jobs(job_id),
  allocated_amount NUMERIC(15,2) DEFAULT 0,           -- phần doanh thu của job này trong HĐ
  UNIQUE (invoice_id, job_id)
);
CREATE INDEX IF NOT EXISTS idx_ar_invoice_jobs_job ON ar_invoice_jobs(job_id);

-- ---------- AP: PHẢI TRẢ ----------
CREATE TABLE IF NOT EXISTS ap_bills (
  bill_id        SERIAL PRIMARY KEY,
  bill_no        TEXT UNIQUE,
  vendor_id      INT REFERENCES vendors(vendor_id),   -- 1 trong 2: vendor HOẶC employee
  employee_id    INT REFERENCES employees(employee_id),
  period_from    DATE,
  period_to      DATE,
  total_amount   NUMERIC(15,2) DEFAULT 0,
  currency       TEXT DEFAULT 'VND',
  payment_status TEXT NOT NULL DEFAULT 'unpaid'
                 CHECK (payment_status IN ('unpaid','partial','paid')),
  paid_amount    NUMERIC(15,2) DEFAULT 0,
  paid_date      DATE,
  due_date       DATE,                                -- hạn thanh toán (gắn rule khấu trừ VAT)
  note           TEXT,
  created_by     INT REFERENCES users(user_id),
  created_at     TIMESTAMPTZ DEFAULT now(),
  updated_at     TIMESTAMPTZ DEFAULT now(),
  CHECK (vendor_id IS NOT NULL OR employee_id IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS ap_bill_items (
  id       SERIAL PRIMARY KEY,
  bill_id  INT NOT NULL REFERENCES ap_bills(bill_id) ON DELETE CASCADE,
  cost_id  INT NOT NULL REFERENCES job_costs(cost_id),
  amount   NUMERIC(15,2) DEFAULT 0,
  UNIQUE (bill_id, cost_id)
);
CREATE INDEX IF NOT EXISTS idx_ap_bill_items_cost ON ap_bill_items(cost_id);

-- ---------- VIEW: trạng thái AR của từng job ----------
-- Job nào đã xuất HĐ / đã thu / chưa xuất
CREATE OR REPLACE VIEW v_job_ar_status AS
SELECT j.job_id, j.job_no, j.customer_id, j.total_revenue,
  aij.invoice_id,
  inv.invoice_no,
  inv.payment_status,
  CASE
    WHEN aij.invoice_id IS NULL THEN 'CHUA_XUAT_HD'
    WHEN inv.payment_status = 'paid' THEN 'DA_THU'
    WHEN inv.payment_status = 'partial' THEN 'THU_MOT_PHAN'
    ELSE 'DA_XUAT_CHO_THU'
  END AS ar_state
FROM jobs j
LEFT JOIN ar_invoice_jobs aij ON aij.job_id = j.job_id
LEFT JOIN ar_invoices inv ON inv.invoice_id = aij.invoice_id;

-- ---------- VIEW: chi phí vendor CHƯA nằm trong bảng kê nào ----------
-- Dùng cho nút "Xuất bảng kê vendor X"
-- View thông minh: nhận diện số tờ khai theo loại dịch vụ (CUS gom về cột Số TK,
-- tránh nhầm với B/L-AWB / Số HĐ do data nhập lẫn cột). Fallback service_type
-- từ job_services đại diện khi job_cost không gắn svc_id.
DROP VIEW IF EXISTS v_ap_unbilled_costs;
CREATE VIEW v_ap_unbilled_costs AS
WITH job_svc AS (
  SELECT DISTINCT ON (job_id) job_id, service_type_code, cd_no, bl_awb_no, route,
    origin_address, dest_address, vehicle_id, driver_id, invoice_numbers
  FROM job_services ORDER BY job_id, svc_id
)
SELECT jc.cost_id, jc.job_id, j.job_no, jc.svc_id,
  jc.cost_name, jc.vendor_id, v.short_name AS vendor_name,
  jc.buying_rate, jc.quantity,
  (jc.buying_rate * COALESCE(jc.quantity,1)) AS amount,
  jc.is_reimbursement, jc.created_at::date AS cost_date,
  veh.plate_number,
  COALESCE(s.route, js.route) AS route,
  COALESCE(s.origin_address, js.origin_address) AS origin_address,
  COALESCE(s.dest_address, js.dest_address) AS dest_address,
  COALESCE(s.service_type_code, js.service_type_code) AS service_type_code,
  dr.full_name AS driver_name,
  CASE
    WHEN COALESCE(s.service_type_code, js.service_type_code) LIKE 'CUS%' THEN
      COALESCE(s.cd_no, js.cd_no, s.bl_awb_no, js.bl_awb_no, j.invoice_number)
    ELSE COALESCE(s.cd_no, js.cd_no)
  END AS declaration_no,
  CASE WHEN COALESCE(s.service_type_code, js.service_type_code) LIKE 'CUS%' THEN NULL
       ELSE COALESCE(s.bl_awb_no, js.bl_awb_no) END AS bl_awb_no,
  CASE WHEN COALESCE(s.service_type_code, js.service_type_code) LIKE 'CUS%' THEN NULL
       ELSE j.invoice_number END AS job_invoice_no,
  COALESCE(s.invoice_numbers, js.invoice_numbers) AS invoice_numbers,
  (COALESCE(s.service_type_code, js.service_type_code) LIKE 'CUS%') AS is_customs
FROM job_costs jc
JOIN jobs j ON j.job_id = jc.job_id
LEFT JOIN vendors v ON v.vendor_id = jc.vendor_id
LEFT JOIN job_services s ON s.svc_id = jc.svc_id
LEFT JOIN job_svc js ON js.job_id = jc.job_id
LEFT JOIN vehicles veh ON veh.vehicle_id = COALESCE(s.vehicle_id, js.vehicle_id)
LEFT JOIN drivers dr ON dr.driver_id = COALESCE(s.driver_id, js.driver_id)
WHERE jc.buying_rate > 0
  AND NOT EXISTS (SELECT 1 FROM ap_bill_items abi WHERE abi.cost_id = jc.cost_id);

-- Config notify kế toán (Telegram/Email)
CREATE TABLE IF NOT EXISTS ap_notify_config (
  id SERIAL PRIMARY KEY,
  role TEXT DEFAULT 'accountant',
  telegram_id TEXT,
  email TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ---------- TRIGGER: tự set payment_status theo paid_amount ----------
CREATE OR REPLACE FUNCTION sync_ar_payment_status()
RETURNS TRIGGER AS $$
BEGIN
  IF COALESCE(NEW.paid_amount,0) <= 0 THEN
    NEW.payment_status := 'unpaid';
  ELSIF NEW.paid_amount >= NEW.total AND NEW.total > 0 THEN
    NEW.payment_status := 'paid';
  ELSE
    NEW.payment_status := 'partial';
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION sync_ap_payment_status()
RETURNS TRIGGER AS $$
BEGIN
  IF COALESCE(NEW.paid_amount,0) <= 0 THEN
    NEW.payment_status := 'unpaid';
  ELSIF NEW.paid_amount >= NEW.total_amount AND NEW.total_amount > 0 THEN
    NEW.payment_status := 'paid';
  ELSE
    NEW.payment_status := 'partial';
  END IF;
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_ar_payment_status ON ar_invoices;
CREATE TRIGGER trg_ar_payment_status
  BEFORE INSERT OR UPDATE OF paid_amount, total ON ar_invoices
  FOR EACH ROW EXECUTE FUNCTION sync_ar_payment_status();

DROP TRIGGER IF EXISTS trg_ap_payment_status ON ap_bills;
CREATE TRIGGER trg_ap_payment_status
  BEFORE INSERT OR UPDATE OF paid_amount, total_amount ON ap_bills
  FOR EACH ROW EXECUTE FUNCTION sync_ap_payment_status();
