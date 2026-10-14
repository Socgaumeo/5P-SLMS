-- 14/10/2026 (Khánh): kỳ đối chiếu / hạn thanh toán theo hợp đồng/thoả thuận của TỪNG KHÁCH.
-- KPI bước "Đối chiếu, thanh toán" lấy kỳ của job/dịch vụ trước, không có thì lấy cột này.
-- Cách ghi (chữ tự do, KPI đọc SỐ CUỐI làm ngày chốt):
--   'cuối tháng'                         -> hạn cuối tháng giao hàng
--   '26 tháng trước -> 25 tháng này'     -> chốt ngày 25 (giao sau 25 thì sang 25 tháng sau)
-- Trống = chưa biết -> Sen hỏi người phụ trách, có rồi mới lưu.
-- customers.payment_terms (=30 mặc định cho mọi khách) KHÔNG phải kỳ đối chiếu, giữ nguyên.

ALTER TABLE customers ADD COLUMN IF NOT EXISTS ky_doi_chieu TEXT;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS ky_doi_chieu_nguon TEXT;  -- hợp đồng / báo giá / ai xác nhận, ngày nào

UPDATE customers SET ky_doi_chieu = 'cuối tháng',
       ky_doi_chieu_nguon = 'chị Hà (8887896178) báo 14/10/2026: bảng kê/debit Meiko làm theo kỳ cuối tháng'
 WHERE customer_id = 32 AND ky_doi_chieu IS NULL;

UPDATE customers SET ky_doi_chieu = '26 tháng trước -> 25 tháng này',
       ky_doi_chieu_nguon = 'chị Hằng 03/08 + 12/08/2026: bảng kê tháng N = 26/(N-1) -> 25/N, áp cả XK và NK'
 WHERE customer_id = 46 AND ky_doi_chieu IS NULL;

-- Kiểm:
-- SELECT customer_id, short_name, ky_doi_chieu, ky_doi_chieu_nguon FROM customers WHERE ky_doi_chieu IS NOT NULL;
