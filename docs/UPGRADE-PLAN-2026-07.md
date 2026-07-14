# SLMS Upgrade Plan — So sánh TMS hiện đại & Đề xuất nâng cấp
> Ngày: 2026-07-14 · Người soạn: Sen · Đối tượng: Khánh (5P Vietnam)

## 0. Tóm tắt điều hành (TL;DR)

SLMS hiện là hệ **chat-first, AI-driven** rất khác biệt: nhân viên nhắn Telegram → AI (deepseek/claude/gemini) tạo job, parse rate sheet, xuất bảng kê/debit. Đây là lợi thế lớn (UX thấp ma sát, không cần training form phức tạp) mà TMS truyền thống KHÔNG có.

**Nhưng** SLMS đang thiếu 3 nhóm nền tảng mà mọi TMS nghiêm túc đều có:
1. **Data integrity** — job mồ côi, thiếu giá, không validate bắt buộc (đã xảy ra thực tế).
2. **Operational visibility** — không có dashboard vận hành, không tracking realtime, không alerting chủ động.
3. **Financial closing loop** — có debit note nhưng thiếu AR/AP, công nợ, P&L per job đúng nghĩa.

**Khuyến nghị:** KHÔNG chạy theo feature enterprise (CargoWise/Descartes). Ưu tiên **củng cố nền tảng data + đóng vòng tài chính + visibility** cho đúng quy mô SME. Roadmap 3 phase, ~4-6 tháng.

---

## 1. Hiện trạng kiến trúc (dựa trên code thật)

| Lớp | Công nghệ | Quy mô | Nhận xét |
|-----|-----------|--------|----------|
| Backend | FastAPI (Python), 93 file | jobs/rates/exports/chat/telegram/debit | Trưởng thành, nhiều logic nghiệp vụ export Excel |
| Frontend | React + Vite | **20 file** (chat, admin, debit, documents) | RẤT mỏng — chưa phải app quản lý đúng nghĩa |
| DB | Supabase Postgres | ~20 bảng nghiệp vụ + NocoDB (nc_*) | Schema tốt: jobs→job_services→job_costs, rates, surcharges |
| AI | Claude/DeepSeek/Gemini | intent → extract → validate → pipeline | Điểm mạnh nhất, khác biệt thị trường |
| Kênh | Telegram bot | webhook + file downloader | Kênh nhập chính, thay cho form |
| Admin data | NocoDB | grid view trên cùng DB | Lớp CRUD thủ công |

**Domain model cốt lõi:**
`jobs` (lô hàng) → `job_services` (dịch vụ trong lô) → `job_costs` (chi phí/doanh thu chi tiết). Rate: `customer_rates` / `vendor_rates` + surcharges. Master: service_types, statuses, vehicle_types, routes, prices.

---

## 2. So sánh theo 10 trục năng lực TMS

Chuẩn tham chiếu: CargoWise, Magaya, Shipsy, Locus, Descartes, Freightos, GoComet, Track-POD.

### Trục 1 — Order/Job Lifecycle ⚠️ (P0 cho data-integrity)
- **Hiện có:** tạo job qua chat, assign vehicle, complete, cancel, đổi customer, thêm service, sync status.
- **Gap:** không enforce bắt buộc field (giá mua/bán trống — incident 14/07); job tạo lẻ không atomic (job mồ côi — incident 09/07 đã có rule nhưng chưa enforce ở DB); không có state machine rõ ràng (DRAFT→CONFIRMED→DISPATCHED→IN_TRANSIT→DELIVERED→CLOSED); thiếu SLA/deadline theo từng chặng.
- **Đề xuất:** (a) **DB constraint + trigger** chặn job_services thiếu buying/selling khi status ≥ CONFIRMED; (b) state machine chuẩn + audit mỗi lần đổi state; (c) required-field matrix theo loại dịch vụ.

### Trục 2 — Dispatch & Route Optimization ❌
- **Hiện có:** điều xe thủ công (nhân viên nhắn "xe 98H06534"), lookup driver, gán driver_id.
- **Gap:** không gợi ý xe theo tải trọng/vị trí; không tối ưu tuyến đa điểm; không thấy xe rảnh/bận realtime; không quản lý capacity đội xe.
- **Đề xuất:** (a) **Bảng điều xe (dispatch board)** — kéo-thả job vào xe, thấy trạng thái đội xe theo ngày; (b) gợi ý loại xe tự động từ CBM/GW (đã có bảng quy đổi trong TOOLS.md — codify vào API); (c) sau này: tích hợp route API (Google/GraphHopper) cho tuyến nhiều điểm.

### Trục 3 — Real-time Tracking / Telematics ❌
- **Hiện có:** không có. Status cập nhật thủ công qua chat.
- **Gap:** khách không biết hàng ở đâu; không GPS; không milestone tự động; không ETA động.
- **Đề xuất:** (a) **Milestone tracking** thủ công trước (tài xế/nhân viên bấm nút hoặc nhắn: đã lấy hàng / qua cửa khẩu / đã giao) → timeline per job; (b) link tracking chia sẻ cho khách; (c) sau: tích hợp GPS đội xe (nhiều xe VN đã có thiết bị GSHTP — pull API).

### Trục 4 — Financial: AR/AP, Invoicing, P&L ⚠️ (P0 — đóng vòng tiền)
- **Hiện có:** debit note generator + template Excel; job_costs (buying/selling, is_reimbursement).
- **Gap:** không có **công nợ phải thu (AR) / phải trả (AP)** theo khách/vendor; không theo dõi đã xuất hóa đơn / đã thu / quá hạn; không **P&L per job** tự động (lãi/lỗ từng lô); VAT tính tay.
- **Đề xuất:** (a) **AR/AP ledger** — mỗi debit note → khoản phải thu; mỗi vendor cost → phải trả; trạng thái (chưa xuất/đã xuất/đã thu/quá hạn); (b) **P&L dashboard per job & per customer** (revenue − cost, margin %); (c) aging report công nợ (30/60/90 ngày); (d) VAT tự động 10% khi xuất.

### Trục 5 — Customer Portal / Self-service ❌
- **Hiện có:** không. Mọi tương tác qua nhân viên.
- **Gap:** khách không tự tra cứu lô hàng, không tự tải chứng từ, không tự xin báo giá.
- **Đề xuất:** (P2) portal đơn giản (hoặc bot Telegram riêng cho khách) — tra status lô, tải debit/chứng từ, xem lịch sử. Tận dụng chính hạ tầng chat sẵn có.

### Trục 6 — Document & Customs ⚠️
- **Hiện có:** upload/download tài liệu, phân loại; export bảng kê theo khách (MEIKO/DAINESE...); parse tờ khai HQ.
- **Gap:** chưa OCR chứng từ đầu vào (invoice/packing list/AN → tự điền job); chưa liên thông VNACCS/ECUS; chưa quản lý vòng đời chứng từ (thiếu/đủ bộ hồ sơ).
- **Đề xuất:** (a) **Checklist bộ chứng từ** per job (đủ/thiếu PO, Invoice, PL, C/O, B/L...); (b) OCR đầu vào bằng chính AI pipeline (đã có Gemini/Claude) → auto-fill; (c) sau: connector ECUS/VNACCS.

### Trục 7 — Analytics / BI / KPI ❌ (P1 — visibility)
- **Hiện có:** vài endpoint dashboard-stats cơ bản; NocoDB grid.
- **Gap:** không có dashboard điều hành (job theo ngày/tuyến/khách, doanh thu, margin, xe sử dụng, on-time %); không KPI nhân viên; không cảnh báo xu hướng.
- **Đề xuất:** (a) **Dashboard vận hành** (React): job hôm nay/tuần, theo status, theo khách, doanh thu/chi phí/margin, top tuyến, sử dụng đội xe; (b) KPI: on-time delivery %, job/nhân viên, doanh thu/khách; (c) export báo cáo tháng tự động.

### Trục 8 — Notification / Alerting ⚠️
- **Hiện có:** gửi Telegram (báo cáo job, ASGL approval), cron.
- **Gap:** alert phần lớn theo lịch, chưa event-driven; chưa cảnh báo bất thường (job thiếu giá, quá hạn giao, công nợ quá hạn, xe detention).
- **Đề xuất:** engine cảnh báo theo sự kiện: job thiếu giá > 24h, sắp đến hạn giao, debit chưa thu quá hạn, xe detention phát sinh.

### Trục 9 — Data Integrity & Validation 🔴 (P0 — nền tảng)
- **Hiện có:** rule ở tầng skill/AI (SKILL.md), validate ở app.
- **Gap nghiêm trọng:** validation nằm ở tầng AI/skill (mềm, dễ bỏ qua khi compact/reset) thay vì **DB constraint** (cứng). Incident thực tế: job mồ côi (09/07), 12 job thiếu giá (14/07), service_type sai code (02/07).
- **Đề xuất:** (a) **Đẩy invariant xuống DB**: FK, CHECK, NOT NULL, trigger atomic job+service, trigger chặn CONFIRMED khi thiếu giá; (b) **reconciliation job** hằng ngày quét bất thường (đã có Job Audit cron — mở rộng); (c) view "sức khỏe dữ liệu" trong dashboard.

### Trục 10 — Integration / EDI / API ⚠️
- **Hiện có:** REST API nội bộ, Telegram, Google Drive upload, NocoDB.
- **Gap:** chưa mở API cho khách/đối tác; chưa EDI hãng tàu/airline; chưa kết nối kế toán (MISA/Fast).
- **Đề xuất:** (P2) API key cho đối tác; connector kế toán VN (MISA/Fast) để đẩy hóa đơn/công nợ; webhook cho khách lớn.

---

## 3. Bảng ưu tiên tổng hợp

| # | Hạng mục | Trục | Ưu tiên | Effort | Lý do |
|---|----------|------|---------|--------|-------|
| 1 | DB constraints + atomic job/service + chặn thiếu giá | 1,9 | **P0** | S-M | Chặn tận gốc incident đã xảy ra |
| 2 | AR/AP ledger + P&L per job | 4 | **P0** | M-L | Đóng vòng tiền, biết lãi/lỗ từng lô |
| 3 | Dashboard vận hành (React) | 7 | **P1** | M | Visibility điều hành, FE đang quá mỏng |
| 4 | Dispatch board + gợi ý loại xe | 2 | **P1** | M | Điều xe đang thủ công 100% |
| 5 | Milestone tracking + link chia sẻ khách | 3 | **P1** | M | Khách hỏi "hàng ở đâu" |
| 6 | Alert engine event-driven | 8 | **P1** | S-M | Cảnh báo chủ động thay vì bị động |
| 7 | Checklist bộ chứng từ + OCR auto-fill | 6 | **P2** | M | Tận dụng AI pipeline sẵn có |
| 8 | Customer portal / bot khách | 5 | **P2** | L | Self-service, giảm tải nhân viên |
| 9 | Connector kế toán (MISA/Fast) + API đối tác | 10 | **P2** | L | Liên thông tài chính |

Effort: S ≤ 1 tuần · M 2-4 tuần · L > 1 tháng.

---

## 4. Roadmap đề xuất

### Phase 1 — Nền tảng (4-6 tuần) · P0
Củng cố data integrity + đóng vòng tài chính. Đây là phần "âm thầm" nhưng quan trọng nhất.
- DB constraints, trigger atomic, chặn thiếu giá.
- AR/AP ledger + P&L per job + aging công nợ.
- Reconciliation/health-check mở rộng.

### Phase 2 — Visibility & Vận hành (6-8 tuần) · P1
Làm dày FE thành app quản lý thật.
- Dashboard vận hành (job/doanh thu/margin/đội xe/on-time).
- Dispatch board + gợi ý loại xe từ CBM/GW.
- Milestone tracking + link chia sẻ khách.
- Alert engine event-driven.

### Phase 3 — Mở rộng & Tự động (8+ tuần) · P2
- Checklist + OCR chứng từ auto-fill.
- Customer portal / bot khách.
- Connector kế toán + API đối tác.

---

## 5. Điểm khác biệt cần GIỮ (đừng đánh mất)

TMS truyền thống bắt nhân viên nhập form phức tạp. SLMS để nhân viên **nhắn tự nhiên**, AI làm phần còn lại. Đây là "moat". Mọi nâng cấp phải **bổ sung tầng cấu trúc BÊN DƯỚI** (DB, tài chính, dashboard) mà **KHÔNG làm mất** trải nghiệm chat-first ở trên. Dashboard/portal là để XEM và QUẢN LÝ; còn NHẬP LIỆU vẫn nên giữ đường chat + AI.

---

## 6. Chốt scope sau feedback Khánh (14/07)

Khánh đã trả lời → thu hẹp scope, LOẠI các đề xuất thừa:

| Đề xuất ban đầu | Quyết định | Lý do |
|-----------------|-----------|-------|
| P&L per job (revenue/cost input) | ✅ ĐÃ CÓ | Job đã có input doanh thu, thu/chi hộ, chi phí rồi |
| AR/AP công nợ | ✅ GIỮ (thu hẹp) | Chỉ thiếu **theo dõi công nợ** → thuộc **module Kế toán** |
| Customer portal (Trục 5) | ❌ BỎ | TMS nội bộ, không cần khách tra cứu |
| Real-time GPS tracking (Trục 3) | ❌ BỎ | 100% xe thuê ngoài, không quản GPS |
| Dispatch board tối ưu đội xe (Trục 2) | ⚠️ GIẢM | Xe thuê ngoài → không quản capacity; chỉ giữ **gợi ý loại xe từ CBM/GW** khi báo giá/điều xe |
| Connector kế toán (MISA/Fast) | ⏸️ TREO | Chưa rõ dùng phần mềm gì, chưa chắc cần kết nối |
| Milestone tracking thủ công | ⚠️ TÙY | Cân nhắc lại — xe thuê ngoài thì cập nhật status qua chat có thể đủ |

### Scope thật sau khi lọc — tập trung 3 mảng:

**A. Data integrity (P0)** — vẫn là ưu tiên cao nhất, incident thật.
- DB constraints + trigger atomic job/service + chặn CONFIRMED khi thiếu giá.
- Reconciliation/health-check mở rộng.

**B. Module Kế toán — theo dõi công nợ (P0/P1)** — đây là gap tài chính DUY NHẤT còn lại.
- Công nợ phải thu (AR) theo khách: mỗi debit note → khoản phải thu, trạng thái (chưa xuất HĐ / đã xuất / đã thu / quá hạn).
- Công nợ phải trả (AP) theo vendor: chi phí mua → khoản phải trả.
- Aging report 30/60/90 ngày.
- (Vì job đã có revenue/cost → P&L per job chỉ cần **tổng hợp lại thành báo cáo**, không phải xây từ đầu.)

**C. Dashboard vận hành nội bộ (P1)** — làm dày FE (đang 20 file).
- Job theo ngày/tuần/status/khách, doanh thu/chi phí/margin, top tuyến.
- Bảng công nợ tổng quan (nối mảng B).
- Alert: job thiếu giá > 24h, debit quá hạn thu, sắp đến hạn giao.

### Còn cần Khánh xác nhận thêm:
1. **Module kế toán công nợ**: xây TRONG SLMS, hay chỉ xuất dữ liệu để kế toán nhập phần mềm riêng? (quyết định A hay B: SLMS thành nơi quản công nợ, hay chỉ là nguồn số liệu)
2. Có cần **màn hình cho kế toán** thao tác (đánh dấu đã thu/đã trả) trong SLMS không?
