# 🚚 MODULE 2.1: JOB LIFECYCLE (Chat UI + AI Workflow)

## 📋 Mục lục
1. [Workflow Overview](#1-workflow-overview)
2. [Job Creation via Chat UI](#2-job-creation-via-chat-ui)
3. [Vehicle Assignment via Chat UI](#3-vehicle-assignment-via-chat-ui)
4. [Job Completion](#4-job-completion)
5. [Database Schema](#5-database-schema)

---

## 1. Workflow Overview

### 1.1 Core Principle: Manual-Assisted AI

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    SLMS WORKFLOW PRINCIPLE                                       │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                          │   │
│   │   "OPS/CS paste nội dung vào Chat UI → AI xử lý → OPS review → Confirm" │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ❌ KHÔNG sử dụng:                                                             │
│   ─────────────────                                                             │
│   • n8n webhook                                                                 │
│   • Zalo Bot tự động                                                           │
│   • Auto-reply                                                                  │
│                                                                                  │
│   ✅ SỬ DỤNG:                                                                   │
│   ───────────                                                                   │
│   • SLMS Chat UI (giao diện chat trên web)                                     │
│   • AI Service (Gemini 2.0 Flash / DeepSeek)                                   │
│   • Manual copy/paste từ/đến Zalo                                              │
│   • Human review trước mọi action                                              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Complete Job Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        COMPLETE JOB FLOW                                         │
│                                                                                  │
│   ┌─────────┐                                                                   │
│   │  ZALO   │  Customer gửi booking (text/file/image)                          │
│   │ Customer│                                                                   │
│   └────┬────┘                                                                   │
│        │ OPS copy/save                                                          │
│        ▼                                                                        │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │                    SLMS CHAT UI                                         │  │
│   │                                                                          │  │
│   │  [Paste text / Upload file / Upload image]                              │  │
│   │                     │                                                    │  │
│   │                     ▼                                                    │  │
│   │  ┌──────────────────────────────────────────────────────────────────┐   │  │
│   │  │  AI SERVICE (Gemini/DeepSeek)                                    │   │  │
│   │  │                                                                   │   │  │
│   │  │  • Detect Intent: CREATE_JOB                                     │   │  │
│   │  │  • Extract: customer, date, time, route, cargo, invoices        │   │  │
│   │  │  • Confidence: 0.95                                              │   │  │
│   │  └──────────────────────────────────────────────────────────────────┘   │  │
│   │                     │                                                    │  │
│   │                     ▼                                                    │  │
│   │  ┌──────────────────────────────────────────────────────────────────┐   │  │
│   │  │  REVIEW FORM (Pre-filled by AI)                                  │   │  │
│   │  │                                                                   │   │  │
│   │  │  Customer: [DREAMTECH ▼]    Date: [17/01/2026]                  │   │  │
│   │  │  Route: [MK-HN ▼]           Time: [22:00]                        │   │  │
│   │  │  Vehicle: [1.25T ▼]         Vendor: [Tam Bảo ▼] ← OPS chọn     │   │  │
│   │  │  ...                                                             │   │  │
│   │  └──────────────────────────────────────────────────────────────────┘   │  │
│   │                     │                                                    │  │
│   │              [Cancel] [Edit] [✓ Create Job]                             │  │
│   │                                  │                                       │  │
│   │                                  ▼                                       │  │
│   │  ┌──────────────────────────────────────────────────────────────────┐   │  │
│   │  │  ✅ Job TRK-2601-0089 Created                                    │   │  │
│   │  │                                                                   │   │  │
│   │  │  📋 Message for Vendor (Tam Bảo):              [Copy]           │   │  │
│   │  │  ───────────────────────────────                                 │   │  │
│   │  │  🚛 YÊU CẦU XE - DRT1                                           │   │  │
│   │  │  📅 Ngày: 17/01/2026                                            │   │  │
│   │  │  ⏰ Giờ: 22:00                                                  │   │  │
│   │  │  ...                                                             │   │  │
│   │  └──────────────────────────────────────────────────────────────────┘   │  │
│   │                                                                          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│        │ OPS click [Copy]                                                      │
│        ▼                                                                        │
│   ┌─────────┐                                                                   │
│   │  ZALO   │  OPS paste message vào group vendor                              │
│   │ Vendor  │                                                                   │
│   └─────────┘                                                                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Job Status Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          JOB STATUS FLOW                                         │
│                                                                                  │
│   ┌───────┐     ┌─────────┐     ┌───────────┐     ┌────────────┐               │
│   │ DRAFT │────►│ PENDING │────►│ CONFIRMED │────►│ DISPATCHED │               │
│   └───────┘     └─────────┘     └───────────┘     └─────┬──────┘               │
│       │              │               │                   │                       │
│   Created by     Waiting for      Vendor           Vehicle                      │
│   OPS manually   vendor response  confirmed        assigned                     │
│                                                          │                       │
│                                                          ▼                       │
│                                                   ┌────────────┐                 │
│                                                   │ IN_TRANSIT │                 │
│                                                   └─────┬──────┘                 │
│                                                         │                        │
│                                                         ▼                        │
│                                                   ┌───────────┐                  │
│                                                   │ DELIVERED │                  │
│                                                   └─────┬─────┘                  │
│                                                         │                        │
│                                                         ▼                        │
│                                                   ┌───────────┐                  │
│                                                   │ COMPLETED │                  │
│                                                   └───────────┘                  │
│                                                                                  │
│       └──────────────┴───────────────┴─────────► ┌───────────┐                  │
│                    (Can cancel at any stage)     │ CANCELLED │                  │
│                                                  └───────────┘                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Job Creation via Chat UI

### 2.1 Input Types Supported

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    SUPPORTED INPUT TYPES                                         │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📝 TYPE 1: TEXT (Ngôn ngữ tự nhiên)                                     │   │
│   │                                                                          │   │
│   │   OPS copy tin nhắn từ Zalo, paste vào Chat UI:                         │   │
│   │                                                                          │   │
│   │   "Ngày mai 22h cần xe 1.25T chở 2 kiện linh kiện từ DRT1              │   │
│   │    ra Nội Bài. Invoice: 260116DRT-001, 260116DRT-002"                   │   │
│   │                                                                          │   │
│   │   AI Processing:                                                        │   │
│   │   • NLP Intent Detection → CREATE_JOB (0.95)                           │   │
│   │   • Entity Extraction → customer, date, time, cargo, invoices          │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📄 TYPE 2: EXCEL FILE                                                   │   │
│   │                                                                          │   │
│   │   Customer gửi file "Phiếu book xe.xlsx" qua Zalo                       │   │
│   │   OPS download và upload lên Chat UI                                    │   │
│   │                                                                          │   │
│   │   ┌────────────────────────────────────────────────────────────────┐   │   │
│   │   │ A          │ B              │ C      │ D       │ E             │   │   │
│   │   ├────────────┼────────────────┼────────┼─────────┼───────────────┤   │   │
│   │   │ Ngày       │ 17/01/2026     │        │         │               │   │   │
│   │   │ Giờ        │ 22:00          │        │         │               │   │   │
│   │   │ Invoice    │ 260116DRT-001  │        │         │               │   │   │
│   │   │ Hàng hóa   │ Linh kiện      │ 2 kiện │         │               │   │   │
│   │   │ Loại xe    │ 1.25T          │        │         │               │   │   │
│   │   │ Giao tại   │ Sân bay Nội Bài│        │         │               │   │   │
│   │   └────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   │   AI Processing:                                                        │   │
│   │   • Parse Excel cells → Structured data                                │   │
│   │   • Map columns to entities                                            │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📷 TYPE 3: IMAGE (Screenshot)                                           │   │
│   │                                                                          │   │
│   │   OPS chụp màn hình tin nhắn Zalo hoặc file Excel                       │   │
│   │   Upload image lên Chat UI                                              │   │
│   │                                                                          │   │
│   │   ┌────────────────────────────────────────────────────────────────┐   │   │
│   │   │  📷 [Screenshot of Zalo message or Excel]                      │   │   │
│   │   └────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   │   AI Processing:                                                        │   │
│   │   • Gemini Vision / DeepSeek VL: OCR → Extract text                   │   │
│   │   • Then NLP processing on extracted text                              │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Chat UI Flow: Create Job

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    CHAT UI: CREATE JOB FLOW                                      │
│                                                                                  │
│   ╔═════════════════════════════════════════════════════════════════════════╗   │
│   ║  SLMS - AI ASSISTANT                                           [≡]     ║   │
│   ╠═════════════════════════════════════════════════════════════════════════╣   │
│   ║                                                                          ║   │
│   ║  ┌────────────────────────────────────────────────────────────────────┐ ║   │
│   ║  │                     CONVERSATION                                   │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  │  ┌─────────────────────────────────────────────────────────────┐  │ ║   │
│   ║  │  │ 👤 OPS (21:30)                                              │  │ ║   │
│   ║  │  │                                                              │  │ ║   │
│   ║  │  │ Ngày mai 22h cần xe 1.25T chở 2 kiện linh kiện từ DRT1     │  │ ║   │
│   ║  │  │ ra Nội Bài. Invoice: 260116DRT-001, 260116DRT-002          │  │ ║   │
│   ║  │  └─────────────────────────────────────────────────────────────┘  │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  │  ┌─────────────────────────────────────────────────────────────┐  │ ║   │
│   ║  │  │ 🤖 AI Assistant (21:30)                                     │  │ ║   │
│   ║  │  │                                                              │  │ ║   │
│   ║  │  │ Tôi đã nhận diện đây là yêu cầu TẠO JOB mới.               │  │ ║   │
│   ║  │  │                                                              │  │ ║   │
│   ║  │  │ 📊 Thông tin trích xuất:                                    │  │ ║   │
│   ║  │  │ ───────────────────────                                     │  │ ║   │
│   ║  │  │ • Khách hàng: DREAMTECH (DRT1)                             │  │ ║   │
│   ║  │  │ • Ngày: 17/01/2026 (ngày mai)                              │  │ ║   │
│   ║  │  │ • Giờ: 22:00                                               │  │ ║   │
│   ║  │  │ • Tuyến: MK-HN (Quang Minh → Nội Bài)                     │  │ ║   │
│   ║  │  │ • Loại xe: 1.25T                                           │  │ ║   │
│   ║  │  │ • Hàng: Linh kiện điện tử                                  │  │ ║   │
│   ║  │  │ • Số lượng: 2 kiện                                         │  │ ║   │
│   ║  │  │ • Invoice: 260116DRT-001, 260116DRT-002                    │  │ ║   │
│   ║  │  │                                                              │  │ ║   │
│   ║  │  │ Confidence: 95%                                             │  │ ║   │
│   ║  │  │                                                              │  │ ║   │
│   ║  │  └─────────────────────────────────────────────────────────────┘  │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  └────────────────────────────────────────────────────────────────────┘ ║   │
│   ║                                                                          ║   │
│   ║  ┌────────────────────────────────────────────────────────────────────┐ ║   │
│   ║  │                    REVIEW & EDIT FORM                             │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  │  Customer:    [DREAMTECH (DRT1)          ▼]                       │ ║   │
│   ║  │  Date:        [17/01/2026               📅]                       │ ║   │
│   ║  │  Time:        [22:00                    🕐]                       │ ║   │
│   ║  │  Route:       [MK-HN                    ▼]                        │ ║   │
│   ║  │  Vehicle:     [1.25T                    ▼]                        │ ║   │
│   ║  │  Cargo:       [Linh kiện điện tử          ]                       │ ║   │
│   ║  │  Package:     [2 kiện                     ]                       │ ║   │
│   ║  │  Invoices:    [260116DRT-001, 260116DRT-002]                      │ ║   │
│   ║  │  ─────────────────────────────────────────────                    │ ║   │
│   ║  │  Vendor:      [Tam Bảo                  ▼]  ← OPS chọn vendor    │ ║   │
│   ║  │  ─────────────────────────────────────────────                    │ ║   │
│   ║  │  Est. Cost:   850,000 VND                                         │ ║   │
│   ║  │  Est. Price:  1,030,000 VND                                       │ ║   │
│   ║  │  Margin:      21.2%                                               │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  │          [❌ Hủy]    [✏️ Sửa]    [✅ Tạo Job]                      │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  └────────────────────────────────────────────────────────────────────┘ ║   │
│   ║                                                                          ║   │
│   ╚═════════════════════════════════════════════════════════════════════════╝   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 After Job Created: Copy Message

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    AFTER JOB CREATED                                             │
│                                                                                  │
│   ╔═════════════════════════════════════════════════════════════════════════╗   │
│   ║                                                                          ║   │
│   ║  ┌────────────────────────────────────────────────────────────────────┐ ║   │
│   ║  │ 🤖 AI Assistant (21:31)                                            │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  │ ✅ Đã tạo Job TRK-2601-0089 thành công!                           │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  │ ┌─────────────────────────────────────────────────────────────┐   │ ║   │
│   ║  │ │ 📋 TIN NHẮN GỬI VENDOR (Tam Bảo)                   [Copy] │   │ ║   │
│   ║  │ │                                                             │   │ ║   │
│   ║  │ │ 🚛 YÊU CẦU XE - DRT1                                       │   │ ║   │
│   ║  │ │                                                             │   │ ║   │
│   ║  │ │ 📅 Ngày: 17/01/2026                                        │   │ ║   │
│   ║  │ │ ⏰ Giờ: 22:00                                              │   │ ║   │
│   ║  │ │ 📦 Invoice: 260116DRT-001, 260116DRT-002                   │   │ ║   │
│   ║  │ │ 📋 Hàng: Linh kiện điện tử - 2 kiện                       │   │ ║   │
│   ║  │ │ 🚗 Loại xe: 1.25T                                         │   │ ║   │
│   ║  │ │ 📍 Giao: Sân bay Nội Bài                                  │   │ ║   │
│   ║  │ │                                                             │   │ ║   │
│   ║  │ │ Vui lòng điều xe và phản hồi thông tin lái xe.            │   │ ║   │
│   ║  │ │                                                             │   │ ║   │
│   ║  │ └─────────────────────────────────────────────────────────────┘   │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  │ 💡 Hướng dẫn: Click [Copy] rồi paste vào Zalo group Tam Bảo     │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  └────────────────────────────────────────────────────────────────────┘ ║   │
│   ║                                                                          ║   │
│   ╚═════════════════════════════════════════════════════════════════════════╝   │
│                                                                                  │
│   Next Step:                                                                     │
│   1. OPS click [Copy]                                                           │
│   2. Mở Zalo group "Tam Bảo"                                                    │
│   3. Paste message                                                              │
│   4. Chờ vendor phản hồi thông tin xe                                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Vehicle Assignment via Chat UI

### 3.1 Receive Vendor Response

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    VEHICLE ASSIGNMENT FLOW                                       │
│                                                                                  │
│   ┌─────────┐                                                                   │
│   │  ZALO   │  Vendor "Tam Bảo" trả lời:                                       │
│   │ Vendor  │  "BKS 29H 76514 - Nguyễn Việt Đức - 0912.345.678                │
│   └────┬────┘   - CCCD 001234567890"                                           │
│        │                                                                        │
│        │ OPS copy response                                                      │
│        ▼                                                                        │
│   ╔═════════════════════════════════════════════════════════════════════════╗  │
│   ║  SLMS - AI ASSISTANT                                           [≡]     ║  │
│   ╠═════════════════════════════════════════════════════════════════════════╣  │
│   ║                                                                          ║  │
│   ║  ┌────────────────────────────────────────────────────────────────────┐ ║  │
│   ║  │ Context: Job TRK-2601-0089 (đang chờ assign xe)                   │ ║  │
│   ║  └────────────────────────────────────────────────────────────────────┘ ║  │
│   ║                                                                          ║  │
│   ║  ┌────────────────────────────────────────────────────────────────────┐ ║  │
│   ║  │ 👤 OPS (21:45)                                                     │ ║  │
│   ║  │                                                                     │ ║  │
│   ║  │ BKS 29H 76514 - Nguyễn Việt Đức - 0912.345.678                    │ ║  │
│   ║  │ - CCCD 001234567890                                                │ ║  │
│   ║  │                                                                     │ ║  │
│   ║  └────────────────────────────────────────────────────────────────────┘ ║  │
│   ║                                                                          ║  │
│   ║  ┌────────────────────────────────────────────────────────────────────┐ ║  │
│   ║  │ 🤖 AI Assistant (21:45)                                            │ ║  │
│   ║  │                                                                     │ ║  │
│   ║  │ Tôi đã nhận diện đây là thông tin XE/LÁI XE từ vendor.           │ ║  │
│   ║  │                                                                     │ ║  │
│   ║  │ 📊 Thông tin trích xuất:                                           │ ║  │
│   ║  │ ───────────────────────                                            │ ║  │
│   ║  │ • Biển số: 29H 76514                                              │ ║  │
│   ║  │ • Tên lái xe: Nguyễn Việt Đức                                    │ ║  │
│   ║  │ • Số điện thoại: 0912.345.678                                    │ ║  │
│   ║  │ • CCCD: 001234567890                                              │ ║  │
│   ║  │                                                                     │ ║  │
│   ║  │ 🔗 Liên kết với: Job TRK-2601-0089                                │ ║  │
│   ║  │    Customer: DREAMTECH (DRT1)                                      │ ║  │
│   ║  │    Date: 17/01/2026 22:00                                         │ ║  │
│   ║  │                                                                     │ ║  │
│   ║  │ Confidence: 92%                                                    │ ║  │
│   ║  │                                                                     │ ║  │
│   ║  └────────────────────────────────────────────────────────────────────┘ ║  │
│   ║                                                                          ║  │
│   ║  ┌────────────────────────────────────────────────────────────────────┐ ║  │
│   ║  │                  REVIEW VEHICLE ASSIGNMENT                        │ ║  │
│   ║  │                                                                     │ ║  │
│   ║  │  Job:           [TRK-2601-0089            ]  (readonly)           │ ║  │
│   ║  │  License Plate: [29H 76514                ]                       │ ║  │
│   ║  │  Driver Name:   [Nguyễn Việt Đức          ]                       │ ║  │
│   ║  │  Driver Phone:  [0912.345.678             ]                       │ ║  │
│   ║  │  Driver CCCD:   [001234567890             ]                       │ ║  │
│   ║  │                                                                     │ ║  │
│   ║  │        [❌ Hủy]    [✏️ Sửa]    [✅ Gán xe & Tạo tin nhắn]         │ ║  │
│   ║  │                                                                     │ ║  │
│   ║  └────────────────────────────────────────────────────────────────────┘ ║  │
│   ║                                                                          ║  │
│   ╚═════════════════════════════════════════════════════════════════════════╝  │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 After Assignment: Customer Message

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    AFTER VEHICLE ASSIGNED                                        │
│                                                                                  │
│   ╔═════════════════════════════════════════════════════════════════════════╗   │
│   ║                                                                          ║   │
│   ║  ┌────────────────────────────────────────────────────────────────────┐ ║   │
│   ║  │ 🤖 AI Assistant (21:46)                                            │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  │ ✅ Đã gán xe cho Job TRK-2601-0089!                               │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  │ Job Status: PENDING → DISPATCHED                                   │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  │ ┌─────────────────────────────────────────────────────────────┐   │ ║   │
│   ║  │ │ 📋 TIN NHẮN GỬI KHÁCH HÀNG (DRT1)                  [Copy] │   │ ║   │
│   ║  │ │                                                             │   │ ║   │
│   ║  │ │ MK-DRT1 / 17.01 / 22:00 / Invoice: 260116DRT-001,          │   │ ║   │
│   ║  │ │ 260116DRT-002 / Linh kiện điện tử / 2 kiện / 1.25T /       │   │ ║   │
│   ║  │ │ BKS: 29H 76514 / Nguyễn Việt Đức - 0912.345.678 -          │   │ ║   │
│   ║  │ │ CCCD: 001234567890                                          │   │ ║   │
│   ║  │ │                                                             │   │ ║   │
│   ║  │ └─────────────────────────────────────────────────────────────┘   │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  │ 💡 Hướng dẫn: Click [Copy] rồi paste vào Zalo group DREAMTECH    │ ║   │
│   ║  │                                                                     │ ║   │
│   ║  └────────────────────────────────────────────────────────────────────┘ ║   │
│   ║                                                                          ║   │
│   ╚═════════════════════════════════════════════════════════════════════════╝   │
│                                                                                  │
│   Next Step:                                                                     │
│   1. OPS click [Copy]                                                           │
│   2. Mở Zalo group "DREAMTECH"                                                  │
│   3. Paste message                                                              │
│   4. Job đã sẵn sàng chạy!                                                      │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Job Completion

### 4.1 Complete Job via Chat UI

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    JOB COMPLETION VIA CHAT UI                                    │
│                                                                                  │
│   Option 1: Natural Language                                                     │
│   ──────────────────────────                                                    │
│                                                                                  │
│   👤 OPS: "Job TRK-2601-0089 đã giao xong lúc 23:30"                           │
│                                                                                  │
│   🤖 AI: Tôi đã nhận diện yêu cầu HOÀN THÀNH JOB.                              │
│                                                                                  │
│          Job: TRK-2601-0089                                                     │
│          Delivery Time: 23:30                                                   │
│                                                                                  │
│          [❌ Hủy]  [✅ Xác nhận hoàn thành]                                     │
│                                                                                  │
│   ─────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│   Option 2: From Job List                                                        │
│   ───────────────────────                                                       │
│                                                                                  │
│   OPS mở Job Detail → Click [Complete Job]                                      │
│                                                                                  │
│   ─────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│   After Completion:                                                              │
│   ─────────────────                                                             │
│                                                                                  │
│   🤖 AI: ✅ Job TRK-2601-0089 đã hoàn thành!                                   │
│                                                                                  │
│          Status: DISPATCHED → COMPLETED                                         │
│          Completed at: 17/01/2026 23:30                                        │
│                                                                                  │
│          Financial Summary:                                                     │
│          • Cost: 850,000 VND                                                   │
│          • Revenue: 1,030,000 VND                                              │
│          • Profit: 180,000 VND (21.2%)                                         │
│                                                                                  │
│          Billing Status: UNBILLED (ready for statement)                        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Database Schema

### 5.1 Jobs Table

```sql
CREATE TABLE jobs (
    id              SERIAL PRIMARY KEY,
    job_number      VARCHAR(20) UNIQUE NOT NULL,    -- TRK-2601-0001
    
    -- Job Type
    job_type        VARCHAR(20) NOT NULL,           -- TRUCKING_SHORT, TRUCKING_LONG, CUSTOMS
    service_id      INTEGER REFERENCES services(id),
    
    -- Customer Info
    customer_id     INTEGER REFERENCES customers(id) NOT NULL,
    customer_code   VARCHAR(20),
    customer_ref    VARCHAR(100),
    
    -- Booking Info
    booking_date    DATE NOT NULL,
    pickup_time     TIME,
    delivery_date   DATE,
    delivery_time   TIME,
    
    -- Route
    route_id        INTEGER REFERENCES routes(id),
    pickup_address  TEXT,
    delivery_address TEXT,
    
    -- Cargo Info
    cargo_type      VARCHAR(50),
    invoice_numbers TEXT,
    package_info    TEXT,
    weight_kg       DECIMAL(10,2),
    volume_cbm      DECIMAL(10,2),
    cargo_value     DECIMAL(15,2),
    special_requirements TEXT,
    
    -- Assignment
    vendor_id       INTEGER REFERENCES vendors(id),
    vehicle_id      INTEGER REFERENCES vehicles(id),
    driver_id       INTEGER REFERENCES drivers(id),
    vehicle_type    VARCHAR(20),
    license_plate   VARCHAR(20),
    driver_name     VARCHAR(100),
    driver_phone    VARCHAR(20),
    driver_id_card  VARCHAR(20),
    
    -- Status
    status          VARCHAR(20) DEFAULT 'DRAFT',
    
    -- Timestamps
    confirmed_at    TIMESTAMP,
    dispatched_at   TIMESTAMP,
    picked_up_at    TIMESTAMP,
    delivered_at    TIMESTAMP,
    completed_at    TIMESTAMP,
    cancelled_at    TIMESTAMP,
    cancel_reason   TEXT,
    
    -- Financials
    cost_amount     DECIMAL(12,2),
    revenue_amount  DECIMAL(12,2),
    profit_amount   DECIMAL(12,2),
    currency        VARCHAR(3) DEFAULT 'VND',
    
    -- Billing Status
    billing_status  VARCHAR(20) DEFAULT 'UNBILLED',
    customer_statement_id INTEGER,
    vendor_statement_id INTEGER,
    
    -- AI Processing Tracking
    ai_source       VARCHAR(20),                    -- CHAT_TEXT, CHAT_FILE, CHAT_IMAGE
    ai_model        VARCHAR(50),                    -- gemini-2.0-flash, deepseek-chat
    ai_confidence   DECIMAL(3,2),
    raw_input       TEXT,                           -- Original input for reference
    
    -- Meta
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by      INTEGER REFERENCES users(id),
    notes           TEXT
);
```

### 5.2 Chat Sessions Table (Track UI interactions)

```sql
CREATE TABLE chat_sessions (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER REFERENCES users(id),
    
    -- Session info
    started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at        TIMESTAMP,
    
    -- Stats
    total_messages  INTEGER DEFAULT 0,
    jobs_created    INTEGER DEFAULT 0,
    assignments_made INTEGER DEFAULT 0
);

CREATE TABLE chat_messages (
    id              SERIAL PRIMARY KEY,
    session_id      INTEGER REFERENCES chat_sessions(id),
    
    -- Message
    role            VARCHAR(10) NOT NULL,           -- USER, ASSISTANT
    content_type    VARCHAR(20) NOT NULL,           -- TEXT, FILE, IMAGE
    content         TEXT,
    file_path       VARCHAR(255),
    
    -- AI Processing
    intent          VARCHAR(50),
    confidence      DECIMAL(3,2),
    entities        JSONB,
    
    -- Linked action
    action_type     VARCHAR(50),                    -- CREATE_JOB, ASSIGN_VEHICLE, etc.
    action_result   JSONB,
    job_id          INTEGER REFERENCES jobs(id),
    
    -- Timestamps
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at    TIMESTAMP
);
```

### 5.3 Generated Messages Table

```sql
CREATE TABLE generated_messages (
    id              SERIAL PRIMARY KEY,
    job_id          INTEGER REFERENCES jobs(id),
    
    -- Message type
    message_type    VARCHAR(50) NOT NULL,           -- VENDOR_DISPATCH, CUSTOMER_CONFIRM, etc.
    recipient_type  VARCHAR(20) NOT NULL,           -- VENDOR, CUSTOMER
    recipient_id    INTEGER,
    recipient_name  VARCHAR(100),
    
    -- Content
    template_code   VARCHAR(50),
    content         TEXT NOT NULL,
    
    -- Status
    is_copied       BOOLEAN DEFAULT FALSE,
    copied_at       TIMESTAMP,
    
    -- Meta
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by      INTEGER REFERENCES users(id)
);
```

---

## 📊 SUMMARY

### Workflow Principle
- **Manual-Assisted AI**: OPS luôn review trước khi thực hiện
- **No automation to Zalo**: Copy/paste thủ công
- **Chat UI is central**: Mọi thao tác qua giao diện chat

### Input Types
1. **Text** - Copy từ Zalo, paste vào chat
2. **Excel** - Upload file booking
3. **Image** - Screenshot tin nhắn hoặc file

### AI Models
- **Primary**: Gemini 2.0 Flash (cost-effective)
- **Alternative**: DeepSeek (competitive pricing)
- **Vision**: Gemini Vision cho OCR ảnh

### Key Actions
1. **Create Job** - Từ booking request
2. **Assign Vehicle** - Từ vendor response
3. **Complete Job** - Khi giao xong
4. **Generate Messages** - Tự động tạo tin nhắn để copy
