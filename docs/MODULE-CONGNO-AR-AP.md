# MODULE CÔNG NỢ (AR/AP) — 5P SLMS
> Draft spec · 2026-07-14 · Sen · CHỜ KHÁNH DUYỆT trước khi build

## 1. Mục tiêu
Theo dõi **công nợ phải thu (AR)** từ khách hàng và **phải trả (AP)** cho vendor, dựa trên dữ liệu job đã có sẵn (`jobs.total_revenue` / `total_cost`, `job_costs`). KHÔNG nhập lại số — kế thừa từ job.

Đây là gap tài chính duy nhất còn lại (job đã có input doanh thu/chi phí/thu-chi hộ; chỉ thiếu lớp theo dõi đã thu/đã trả bao nhiêu, còn nợ bao nhiêu, quá hạn chưa).

## 2. Nguyên tắc
- **1 job → phát sinh công nợ khi COMPLETED** (hoặc khi phát hành invoice). Trước đó chỉ là dự kiến.
- **AR** = tiền khách phải trả 5P = `total_revenue` (gồm cả thu hộ).
- **AP** = tiền 5P phải trả vendor = `total_cost` (gồm cả chi hộ), tách theo `vendor_id` trong `job_costs`.
- Ghi nhận **thanh toán từng phần** (1 hóa đơn trả nhiều lần).
- **Tuổi nợ** (aging): 0-30 / 31-60 / 61-90 / >90 ngày.

## 3. Schema mới (2 bảng)

### 3.1 `ar_invoices` — hóa đơn phải thu (theo khách)
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| invoice_id | serial PK | |
| invoice_no | text unique | số hóa đơn/debit note |
| customer_id | int FK customers | |
| job_id | int FK jobs (nullable) | 1 invoice có thể gộp nhiều job → dùng bảng nối nếu cần |
| issue_date | date | ngày phát hành |
| due_date | date | hạn thanh toán (issue + terms) |
| amount_total | numeric | tổng phải thu (trước/sau VAT — chốt bên dưới) |
| amount_paid | numeric default 0 | đã thu |
| amount_due | numeric GENERATED (total - paid) | còn nợ |
| currency | text default 'VND' | |
| status | text | DRAFT / SENT / PARTIAL / PAID / OVERDUE / CANCELLED |
| vat_rate | numeric | |
| created_by | int FK users | |
| created_at / updated_at | timestamptz | |

### 3.2 `ar_payments` — lần thu tiền
| Cột | Kiểu | Ghi chú |
|-----|------|---------|
| payment_id | serial PK | |
| invoice_id | int FK ar_invoices | |
| pay_date | date | |
| amount | numeric | số tiền lần này |
| method | text | CK/tiền mặt/bù trừ |
| ref_no | text | mã UNC/chứng từ |
| note | text | |
| created_by | int FK users | |

### 3.3 AP — dùng lại cấu trúc tương tự
- `ap_bills` (phải trả vendor) + `ap_payments`. Cột `vendor_id` thay `customer_id`.
- Nguồn: gom `job_costs` theo `vendor_id` cho các job COMPLETED.

> **Lựa chọn đơn giản hơn (khuyến nghị giai đoạn 1):** chưa tách invoice riêng, mà thêm cột trạng thái thu/trả THẲNG vào job + 2 bảng payment. Đỡ phức tạp, đủ để theo dõi công nợ. Chi tiết ở mục 6.

## 4. Cần Khánh chốt (5 câu)
1. **Công nợ tính trên số nào:** trước VAT hay sau VAT (tổng khách thực trả)?
2. **Có phát hành "invoice" trong hệ thống không**, hay chỉ theo dõi thu/trả theo JOB? (5P đã có module debit note — có thể tái dùng).
3. **Terms thanh toán mặc định** mỗi khách (net 30? 45?) — lấy từ đâu? (`customers` có cột payment_terms chưa?)
4. **Thu hộ/chi hộ** có tính vào công nợ không, hay tách riêng "hộ" ra khỏi doanh thu thật?
5. **Ai nhập thanh toán** (kế toán riêng, hay NV tạo job)?

## 5. Màn hình (FE — React, thêm vào frontend hiện có)
- **Dashboard công nợ:** tổng AR, tổng AP, net, quá hạn. Biểu đồ aging.
- **AR theo khách:** list khách + số dư nợ + nút "ghi nhận thu tiền".
- **AP theo vendor:** list vendor + phải trả + nút "ghi nhận trả tiền".
- **Chi tiết 1 khách:** danh sách invoice/job + lịch sử thanh toán.

## 6. Giai đoạn 1 (MVP — khuyến nghị làm trước, nhẹ)
Không tạo bảng invoice phức tạp. Chỉ:
1. Thêm bảng `job_payments` (job_id, direction AR/AP, pay_date, amount, method, ref, created_by).
2. View `v_job_debt`: mỗi job COMPLETED → phải thu (total_revenue) - đã thu (sum AR payment) = còn nợ khách; tương tự AP với vendor.
3. Báo cáo công nợ = query view, group theo customer/vendor + aging theo `jobs.updated_at`/due.
4. 1 màn hình đọc + 1 form ghi payment.

→ Xây nhanh, không đụng schema job hiện có, có ngay số liệu công nợ. Giai đoạn 2 mới tách invoice chính thức nếu cần.

## 7. Rủi ro
- 58 job COMPLETED thiếu giá → công nợ sai cho tới khi điền (đang xử lý).
- Thu hộ/chi hộ lẫn trong total → cần cột `is_reimbursement` (job_costs đã có) để tách nếu muốn báo cáo "doanh thu thật".
- Đối trừ công nợ (khách vừa là vendor) — hiếm, để giai đoạn 2.
