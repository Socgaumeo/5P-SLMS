# 📚 SLMS - HỆ THỐNG QUẢN LÝ LOGISTICS THÔNG MINH

## 🎯 Tổng quan dự án

**SLMS (Smart Logistics Management System)** là hệ thống quản lý logistics toàn diện với AI-powered interface, được thiết kế cho các công ty logistics vận tải tại Việt Nam.

---

## 📦 CẤU TRÚC MODULES

```
SLMS SYSTEM
│
├── 📁 MODULE 1: FOUNDATION (Nền tảng)
│   ├── 1.1 System Infrastructure
│   │   ├── Users & Authentication
│   │   ├── Roles & Permissions  
│   │   ├── Audit Logging
│   │   └── Backup & Recovery
│   │
│   └── 1.2 Master Data
│       ├── Customers (Khách hàng)
│       ├── Vendors (Nhà cung cấp)
│       ├── Drivers (Lái xe)
│       ├── Vehicles/Trucks (Phương tiện)
│       ├── Routes (Tuyến đường)
│       ├── Services (Dịch vụ)
│       └── Rates/Pricing (Bảng giá)
│
├── 📁 MODULE 2: JOB MANAGEMENT (Quản lý Job)
│   ├── 2.1 Job Lifecycle
│   │   ├── Job Creation
│   │   ├── Job Assignment
│   │   ├── Job Execution
│   │   └── Job Completion
│   │
│   ├── 2.2 Service Management
│   │   ├── Service Booking
│   │   ├── Service Tracking
│   │   └── Service Rating
│   │
│   └── 2.3 Communication
│       ├── Customer Communication
│       ├── Vendor Communication
│       └── Internal Notifications
│
├── 📁 MODULE 3: FINANCIAL (Tài chính)
│   ├── 3.1 Pricing Management
│   │   ├── Vendor Rates (Giá mua)
│   │   ├── Customer Rates (Giá bán)
│   │   └── Margin Calculation
│   │
│   ├── 3.2 Statements (Bảng kê)
│   │   ├── Customer Statements
│   │   ├── Vendor Statements
│   │   └── Reconciliation
│   │
│   ├── 3.3 Reports (Báo cáo)
│   │   ├── Operational Reports
│   │   ├── Financial Reports
│   │   └── Performance Reports
│   │
│   └── 3.4 MISA Integration
│       ├── Invoice Sync
│       ├── AP/AR Sync
│       └── Chart of Accounts
│
└── 📁 MODULE 4: AI INTEGRATION (Tích hợp AI)
    ├── 4.1 AI Architecture
    │   ├── AI Service Design
    │   ├── Model Selection
    │   └── Cost Optimization
    │
    ├── 4.2 Intent Detection
    │   ├── Message Classification
    │   ├── Action Routing
    │   └── Context Understanding
    │
    ├── 4.3 Entity Extraction
    │   ├── Text Parsing
    │   ├── Document Parsing
    │   └── Image/OCR Processing
    │
    ├── 4.4 Message Generation
    │   ├── Template System
    │   ├── Dynamic Content
    │   └── Multi-channel Output
    │
    └── 4.5 Workflow Automation
        ├── n8n Integration
        ├── Zalo Bot Automation
        └── Scheduled Tasks
```

---

## 🛠️ TECH STACK

| Component | Technology | Chi phí |
|-----------|------------|---------|
| **Database** | PostgreSQL / Supabase | Free - $25/tháng |
| **Backend** | FastAPI (Python) | Free |
| **Frontend** | NocoDB / AppSheet | Free |
| **Automation** | n8n (self-hosted) | Free |
| **AI Models** | Gemini Flash / Claude | $10-30/tháng |
| **Messaging** | Zalo (via automation) | Free |
| **Hosting** | VPS / Cloud Run | $5-20/tháng |

**Tổng chi phí ước tính: $15-75/tháng (~400K-2M VND)**

---

## 📊 TỔNG QUAN DATABASE

### Core Tables (14 bảng chính)

| # | Table | Mô tả | Module |
|---|-------|-------|--------|
| 1 | `users` | Người dùng hệ thống | M1 |
| 2 | `roles` | Phân quyền | M1 |
| 3 | `customers` | Khách hàng | M1 |
| 4 | `vendors` | Nhà cung cấp | M1 |
| 5 | `drivers` | Lái xe | M1 |
| 6 | `vehicles` | Phương tiện | M1 |
| 7 | `routes` | Tuyến đường | M1 |
| 8 | `rates` | Bảng giá | M1 |
| 9 | `jobs` | Booking/Job | M2 |
| 10 | `job_items` | Chi tiết job | M2 |
| 11 | `statements` | Bảng kê | M3 |
| 12 | `statement_items` | Chi tiết bảng kê | M3 |
| 13 | `ai_logs` | Log AI requests | M4 |
| 14 | `message_templates` | Template tin nhắn | M4 |

---

## 🚀 LỘ TRÌNH TRIỂN KHAI

### Phase 1: Foundation (Tuần 1-2)
- Setup database schema
- Master data management
- User authentication

### Phase 2: Job Management (Tuần 3-4)
- Job lifecycle
- Service booking
- Basic communication

### Phase 3: Financial (Tuần 5-6)
- Pricing management
- Statements generation
- Basic reports

### Phase 4: AI Integration (Tuần 7-8)
- AI service setup
- Intent detection
- Document parsing
- Workflow automation

---

## 📁 DANH SÁCH TÀI LIỆU

| # | File | Mô tả |
|---|------|-------|
| 1 | [01_FOUNDATION/01_SYSTEM_INFRASTRUCTURE.md](./01_FOUNDATION/01_SYSTEM_INFRASTRUCTURE.md) | Users, Roles, Logging |
| 2 | [01_FOUNDATION/02_MASTER_DATA.md](./01_FOUNDATION/02_MASTER_DATA.md) | Customers, Vendors, Drivers, Vehicles |
| 3 | [02_JOB_MANAGEMENT/01_JOB_LIFECYCLE.md](./02_JOB_MANAGEMENT/01_JOB_LIFECYCLE.md) | Job creation to completion |
| 4 | [02_JOB_MANAGEMENT/02_SERVICE_MANAGEMENT.md](./02_JOB_MANAGEMENT/02_SERVICE_MANAGEMENT.md) | Service types and tracking |
| 5 | [02_JOB_MANAGEMENT/03_COMMUNICATION.md](./02_JOB_MANAGEMENT/03_COMMUNICATION.md) | Messaging and notifications |
| 6 | [03_FINANCIAL/01_PRICING_MANAGEMENT.md](./03_FINANCIAL/01_PRICING_MANAGEMENT.md) | Rates management |
| 7 | [03_FINANCIAL/02_STATEMENTS.md](./03_FINANCIAL/02_STATEMENTS.md) | Customer/Vendor statements |
| 8 | [03_FINANCIAL/03_REPORTS.md](./03_FINANCIAL/03_REPORTS.md) | Operational and financial reports |
| 9 | [03_FINANCIAL/04_MISA_INTEGRATION.md](./03_FINANCIAL/04_MISA_INTEGRATION.md) | Accounting integration |
| 10 | [04_AI_INTEGRATION/01_AI_ARCHITECTURE.md](./04_AI_INTEGRATION/01_AI_ARCHITECTURE.md) | AI service design |
| 11 | [04_AI_INTEGRATION/02_INTENT_DETECTION.md](./04_AI_INTEGRATION/02_INTENT_DETECTION.md) | Message classification |
| 12 | [04_AI_INTEGRATION/03_ENTITY_EXTRACTION.md](./04_AI_INTEGRATION/03_ENTITY_EXTRACTION.md) | Data parsing |
| 13 | [04_AI_INTEGRATION/04_MESSAGE_GENERATION.md](./04_AI_INTEGRATION/04_MESSAGE_GENERATION.md) | Auto-generate messages |
| 14 | [04_AI_INTEGRATION/05_WORKFLOW_AUTOMATION.md](./04_AI_INTEGRATION/05_WORKFLOW_AUTOMATION.md) | n8n and automation |

---

*Cập nhật lần cuối: 15/01/2026*
