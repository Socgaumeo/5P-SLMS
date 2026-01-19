# ⚙️ MODULE 4.3: WORKFLOW AUTOMATION (Updated)

## 📋 Mục lục
1. [Workflow Philosophy](#1-workflow-philosophy)
2. [Manual-Assisted AI Flow](#2-manual-assisted-ai-flow)
3. [SLMS Chat Interface](#3-slms-chat-interface)
4. [n8n Role (Backend Only)](#4-n8n-role-backend-only)
5. [Future Automation Roadmap](#5-future-automation-roadmap)

---

## 1. Workflow Philosophy

### 1.1 Current Approach: Manual-Assisted AI

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW PHILOSOPHY                                           │
│                                                                                  │
│   ❌ KHÔNG PHẢI (Full Automation):                                              │
│   ────────────────────────────────                                              │
│                                                                                  │
│   [Zalo] ──auto──► [Bot/Webhook] ──auto──► [AI] ──auto──► [Database]           │
│                                                                                  │
│   Lý do không dùng:                                                             │
│   • Zalo không có official API cho group chat                                   │
│   • Rủi ro bot gửi sai thông tin                                               │
│   • Cần human review trước khi gửi cho khách/vendor                            │
│   • Giai đoạn đầu cần kiểm soát chặt                                           │
│                                                                                  │
│   ─────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│   ✅ ĐÚNG (Manual-Assisted AI):                                                 │
│   ─────────────────────────────                                                 │
│                                                                                  │
│   [Zalo] ──copy──► [OPS/CS] ──paste──► [SLMS UI] ──► [AI] ──► [Review]        │
│                                           │                       │             │
│                                           │              [Confirm/Edit]         │
│                                           │                       │             │
│                                           ▼                       ▼             │
│   [Zalo] ◄──paste── [OPS/CS] ◄──copy── [Generated Message]  [Save to DB]       │
│                                                                                  │
│   Lợi ích:                                                                       │
│   • Human-in-the-loop: luôn có người review                                    │
│   • AI assist: giảm 80% thời gian nhập liệu                                    │
│   • Flexible: dễ xử lý edge cases                                              │
│   • Safe: không lo bot gửi nhầm                                                │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Vai trò của từng thành phần

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    COMPONENT ROLES                                               │
│                                                                                  │
│   Component        │ Role                          │ Automation Level           │
│   ─────────────────┼───────────────────────────────┼─────────────────────────── │
│   Zalo             │ Kênh giao tiếp với KH/Vendor  │ Manual (copy/paste)        │
│   OPS/CS Staff     │ Người vận hành, review        │ Human decision maker       │
│   SLMS UI          │ Giao diện nhập liệu           │ Interactive                │
│   AI Service       │ Xử lý, extract, generate      │ Automated processing       │
│   Database         │ Lưu trữ dữ liệu              │ Automated                  │
│   n8n              │ Backend workflows             │ Automated (internal)       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Manual-Assisted AI Flow

### 2.1 Complete Workflow: Booking → Dispatch → Confirm

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE WORKFLOW                                             │
│                                                                                  │
│   PHASE 1: RECEIVE BOOKING                                                      │
│   ════════════════════════                                                      │
│                                                                                  │
│   ┌─────────────┐                                                               │
│   │    ZALO     │  Customer gửi: "Book xe ngày mai 22h, 2 kiện..."             │
│   │  (Customer) │  hoặc gửi file Excel booking                                  │
│   └──────┬──────┘                                                               │
│          │ OPS thấy message                                                      │
│          │ Copy nội dung / Save file                                            │
│          ▼                                                                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         SLMS UI - CHAT INPUT                            │   │
│   │                                                                          │   │
│   │  ┌───────────────────────────────────────────────────────────────────┐  │   │
│   │  │ 📎 Paste text/image/file here...                                  │  │   │
│   │  │                                                                    │  │   │
│   │  │ "Ngày mai 22h lấy hàng tại DRT1, giao Nội Bài                    │  │   │
│   │  │  Invoice: 260116DRT-001, 260116DRT-002                           │  │   │
│   │  │  2 kiện linh kiện điện tử, cần xe 1.25T"                         │  │   │
│   │  │                                                                    │  │   │
│   │  └───────────────────────────────────────────────────────────────────┘  │   │
│   │                                                                          │   │
│   │  [📷 Image] [📄 File] [🎤 Voice]              [🚀 Process with AI]     │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│          │ Click "Process with AI"                                              │
│          ▼                                                                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         AI PROCESSING                                   │   │
│   │                                                                          │   │
│   │  Intent: CREATE_JOB (confidence: 0.95)                                  │   │
│   │                                                                          │   │
│   │  Extracted Entities:                                                    │   │
│   │  ├── Customer: DRT1 (DREAMTECH)                                        │   │
│   │  ├── Date: 17/01/2026                                                  │   │
│   │  ├── Time: 22:00                                                       │   │
│   │  ├── Invoices: 260116DRT-001, 260116DRT-002                           │   │
│   │  ├── Cargo: Linh kiện điện tử                                         │   │
│   │  ├── Package: 2 kiện                                                   │   │
│   │  ├── Vehicle: 1.25T                                                    │   │
│   │  └── Route: MK-HN (detected from DRT1 + Nội Bài)                      │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│          ▼                                                                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                    OPS REVIEW & CONFIRM                                 │   │
│   │                                                                          │   │
│   │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│   │  │ CREATE NEW JOB                                         [Edit] │   │   │
│   │  │                                                                 │   │   │
│   │  │ Customer:    [DREAMTECH (DRT1)    ▼]                          │   │   │
│   │  │ Date:        [17/01/2026         📅]                          │   │   │
│   │  │ Time:        [22:00              🕐]                          │   │   │
│   │  │ Route:       [MK-HN              ▼]                           │   │   │
│   │  │ Vehicle:     [1.25T              ▼]                           │   │   │
│   │  │ Invoices:    [260116DRT-001, 260116DRT-002]                   │   │   │
│   │  │ Cargo:       [Linh kiện điện tử    ]                          │   │   │
│   │  │ Package:     [2 kiện               ]                          │   │   │
│   │  │                                                                 │   │   │
│   │  │ Vendor:      [Tam Bảo            ▼]  ← OPS chọn vendor        │   │   │
│   │  │                                                                 │   │   │
│   │  │ Est. Cost:   850,000 VND                                       │   │   │
│   │  │ Est. Price:  1,030,000 VND                                     │   │   │
│   │  │ Margin:      21.2%                                             │   │   │
│   │  │                                                                 │   │   │
│   │  └─────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   │            [❌ Cancel]    [✏️ Edit]    [✅ Create Job]                   │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│          │ OPS clicks "Create Job"                                              │
│          ▼                                                                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                    JOB CREATED + MESSAGE GENERATED                      │   │
│   │                                                                          │   │
│   │  ✅ Job TRK-2601-0089 created successfully                              │   │
│   │                                                                          │   │
│   │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│   │  │ 📋 MESSAGE FOR VENDOR (Tam Bảo)                        [Copy] │   │   │
│   │  │                                                                 │   │   │
│   │  │ 🚛 YÊU CẦU XE - DRT1                                          │   │   │
│   │  │                                                                 │   │   │
│   │  │ 📅 Ngày: 17/01/2026                                           │   │   │
│   │  │ ⏰ Giờ: 22:00                                                 │   │   │
│   │  │ 📦 Invoice: 260116DRT-001, 260116DRT-002                      │   │   │
│   │  │ 📋 Hàng: Linh kiện điện tử - 2 kiện                          │   │   │
│   │  │ 🚗 Loại xe: 1.25T                                            │   │   │
│   │  │ 📍 Giao: Sân bay Nội Bài                                     │   │   │
│   │  │                                                                 │   │   │
│   │  │ Vui lòng điều xe và phản hồi thông tin lái xe.               │   │   │
│   │  │                                                                 │   │   │
│   │  └─────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│          │ OPS click "Copy"                                                     │
│          ▼                                                                       │
│   ┌─────────────┐                                                               │
│   │    ZALO     │  OPS paste message vào group Tam Bảo                         │
│   │  (Vendor)   │                                                               │
│   └─────────────┘                                                               │
│                                                                                  │
│                                                                                  │
│   PHASE 2: RECEIVE VEHICLE INFO                                                 │
│   ═════════════════════════════                                                 │
│                                                                                  │
│   ┌─────────────┐                                                               │
│   │    ZALO     │  Vendor trả lời: "BKS 29H 76514 - Nguyễn Việt Đức            │
│   │  (Vendor)   │                   - 0912.345.678 - CCCD 001234567890"         │
│   └──────┬──────┘                                                               │
│          │ OPS copy response                                                     │
│          ▼                                                                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                    SLMS UI - PASTE VENDOR RESPONSE                      │   │
│   │                                                                          │   │
│   │  Context: Job TRK-2601-0089 (đang chờ assign xe)                        │   │
│   │                                                                          │   │
│   │  ┌───────────────────────────────────────────────────────────────────┐  │   │
│   │  │ BKS 29H 76514 - Nguyễn Việt Đức - 0912.345.678                   │  │   │
│   │  │ CCCD 001234567890                                                 │  │   │
│   │  └───────────────────────────────────────────────────────────────────┘  │   │
│   │                                                                          │   │
│   │                                              [🚀 Process with AI]       │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│          ▼                                                                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                    AI EXTRACTS VEHICLE INFO                             │   │
│   │                                                                          │   │
│   │  Intent: ASSIGN_VEHICLE (confidence: 0.92)                              │   │
│   │  Linked to: Job TRK-2601-0089                                           │   │
│   │                                                                          │   │
│   │  Extracted:                                                             │   │
│   │  ├── License Plate: 29H 76514                                          │   │
│   │  ├── Driver Name: Nguyễn Việt Đức                                      │   │
│   │  ├── Driver Phone: 0912.345.678                                        │   │
│   │  └── Driver CCCD: 001234567890                                         │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│          ▼                                                                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                    OPS REVIEW & CONFIRM ASSIGNMENT                      │   │
│   │                                                                          │   │
│   │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│   │  │ ASSIGN VEHICLE TO JOB TRK-2601-0089                    [Edit] │   │   │
│   │  │                                                                 │   │   │
│   │  │ License Plate: [29H 76514          ]                          │   │   │
│   │  │ Driver Name:   [Nguyễn Việt Đức    ]                          │   │   │
│   │  │ Driver Phone:  [0912.345.678       ]                          │   │   │
│   │  │ Driver CCCD:   [001234567890       ]                          │   │   │
│   │  │                                                                 │   │   │
│   │  └─────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   │            [❌ Cancel]    [✏️ Edit]    [✅ Assign & Generate]            │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│          │ OPS clicks "Assign & Generate"                                       │
│          ▼                                                                       │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                    MESSAGE FOR CUSTOMER GENERATED                       │   │
│   │                                                                          │   │
│   │  ✅ Vehicle assigned to Job TRK-2601-0089                               │   │
│   │                                                                          │   │
│   │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│   │  │ 📋 MESSAGE FOR CUSTOMER (DRT1)                         [Copy] │   │   │
│   │  │                                                                 │   │   │
│   │  │ MK-DRT1 / 17.01 / 22:00 / Invoice: 260116DRT-001,              │   │   │
│   │  │ 260116DRT-002 / Linh kiện điện tử / 2 kiện / 1.25T /          │   │   │
│   │  │ BKS: 29H 76514 / Nguyễn Việt Đức - 0912.345.678 -             │   │   │
│   │  │ CCCD: 001234567890                                             │   │   │
│   │  │                                                                 │   │   │
│   │  └─────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│          │                                                                       │
│          │ OPS click "Copy"                                                     │
│          ▼                                                                       │
│   ┌─────────────┐                                                               │
│   │    ZALO     │  OPS paste message vào group DREAMTECH                       │
│   │ (Customer)  │                                                               │
│   └─────────────┘                                                               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. SLMS Chat Interface

### 3.1 UI Components

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SLMS CHAT INTERFACE                                      │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 💬 AI ASSISTANT                                              [Settings] │   │
│   ├─────────────────────────────────────────────────────────────────────────┤   │
│   │                                                                          │   │
│   │  ┌────────────────────────────────────────────────────────────────────┐ │   │
│   │  │                    CONVERSATION HISTORY                            │ │   │
│   │  │                                                                     │ │   │
│   │  │  [21:30] 📥 You pasted:                                           │ │   │
│   │  │  "Ngày mai 22h lấy hàng tại DRT1..."                             │ │   │
│   │  │                                                                     │ │   │
│   │  │  [21:30] 🤖 AI detected: CREATE_JOB                              │ │   │
│   │  │  → Created Job TRK-2601-0089                                      │ │   │
│   │  │  → Generated vendor message                                       │ │   │
│   │  │                                                                     │ │   │
│   │  │  [21:45] 📥 You pasted:                                           │ │   │
│   │  │  "BKS 29H 76514 - Nguyễn Việt Đức..."                           │ │   │
│   │  │                                                                     │ │   │
│   │  │  [21:45] 🤖 AI detected: ASSIGN_VEHICLE                          │ │   │
│   │  │  → Updated Job TRK-2601-0089                                      │ │   │
│   │  │  → Generated customer confirmation                                │ │   │
│   │  │                                                                     │ │   │
│   │  └────────────────────────────────────────────────────────────────────┘ │   │
│   │                                                                          │   │
│   │  ┌────────────────────────────────────────────────────────────────────┐ │   │
│   │  │                         INPUT AREA                                 │ │   │
│   │  │                                                                     │ │   │
│   │  │  Context: [Auto-detect ▼] or [Job: TRK-2601-0089 ▼]              │ │   │
│   │  │  Source:  [Customer: DRT1 ▼] or [Vendor: Tam Bảo ▼]              │ │   │
│   │  │                                                                     │ │   │
│   │  │  ┌──────────────────────────────────────────────────────────────┐ │ │   │
│   │  │  │                                                               │ │ │   │
│   │  │  │  Paste text, image, or drop file here...                     │ │ │   │
│   │  │  │                                                               │ │ │   │
│   │  │  │                                                               │ │ │   │
│   │  │  └──────────────────────────────────────────────────────────────┘ │ │   │
│   │  │                                                                     │ │   │
│   │  │  [📷 Image] [📄 File] [📋 Paste]           [🚀 Process with AI]  │ │   │
│   │  │                                                                     │ │   │
│   │  └────────────────────────────────────────────────────────────────────┘ │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Input Types Supported

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SUPPORTED INPUT TYPES                                    │
│                                                                                  │
│   Type        │ Source              │ AI Processing                             │
│   ────────────┼─────────────────────┼───────────────────────────────────────── │
│   📝 Text     │ Copy from Zalo      │ NLP intent + entity extraction           │
│   📷 Image    │ Screenshot Zalo     │ OCR (Gemini Vision) → Text → NLP         │
│   📄 Excel    │ Download from Zalo  │ Parse cells → Structured data            │
│   📄 PDF      │ Download from Zalo  │ OCR/Extract → Text → NLP                 │
│                                                                                  │
│   ───────────────────────────────────────────────────────────────────────────   │
│                                                                                  │
│   EXAMPLE INPUTS:                                                               │
│                                                                                  │
│   Text (Customer booking):                                                       │
│   "Ngày mai 22h cần xe 1.25T chở 2 kiện linh kiện từ DRT1 ra Nội Bài           │
│    Invoice: 260116DRT-001, 260116DRT-002"                                       │
│                                                                                  │
│   Text (Vendor vehicle info):                                                    │
│   "BKS 29H 76514 - Nguyễn Việt Đức - 0912.345.678 - CCCD 001234567890"         │
│                                                                                  │
│   Image:                                                                         │
│   [Screenshot of Excel booking form from Zalo]                                  │
│                                                                                  │
│   File:                                                                          │
│   [Phiếu book xe.xlsx - Customer booking spreadsheet]                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Frontend API Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND → BACKEND API FLOW                              │
│                                                                                  │
│   SLMS UI (React/Vue)                    SLMS Backend (FastAPI)                 │
│   ───────────────────                    ──────────────────────                 │
│                                                                                  │
│   1. User pastes content                                                        │
│      │                                                                          │
│      ▼                                                                          │
│   ┌─────────────────┐                                                           │
│   │ POST /api/ai/   │ ──────────────────►  ┌─────────────────────┐             │
│   │ process         │                       │ AIService.process() │             │
│   │                 │                       │                     │             │
│   │ {               │                       │ • Detect intent     │             │
│   │   content_type: │                       │ • Extract entities  │             │
│   │     "TEXT",     │                       │ • Match to job      │             │
│   │   content:      │                       │ • Generate response │             │
│   │     "...",      │                       │                     │             │
│   │   source:       │                       └─────────────────────┘             │
│   │     "CUSTOMER", │                                │                          │
│   │   source_id:    │                                │                          │
│   │     "DRT1"      │  ◄─────────────────────────────┘                          │
│   │ }               │                                                           │
│   └─────────────────┘                                                           │
│      │                                                                          │
│      ▼                                                                          │
│   2. Display AI result                                                          │
│      User reviews extracted data                                                │
│      │                                                                          │
│      ▼                                                                          │
│   3. User confirms/edits                                                        │
│      │                                                                          │
│      ▼                                                                          │
│   ┌─────────────────┐                                                           │
│   │ POST /api/jobs  │ ──────────────────►  ┌─────────────────────┐             │
│   │                 │                       │ JobService.create() │             │
│   │ {               │                       │                     │             │
│   │   customer_id,  │                       │ • Validate data     │             │
│   │   booking_date, │                       │ • Calculate pricing │             │
│   │   ...           │                       │ • Save to database  │             │
│   │ }               │                       │ • Generate message  │             │
│   └─────────────────┘                       └─────────────────────┘             │
│      │                                               │                          │
│      ▼                                               │                          │
│   4. Display created job                             │                          │
│      + Generated message for copy         ◄──────────┘                          │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. n8n Role (Backend Only)

### 4.1 n8n KHÔNG dùng cho Zalo

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    n8n ROLE IN SLMS (Backend Only)                               │
│                                                                                  │
│   ❌ KHÔNG dùng n8n cho:                                                        │
│   ─────────────────────                                                         │
│   • Webhook nhận message từ Zalo (không có API)                                │
│   • Auto-reply vào Zalo (không có API)                                         │
│   • Real-time sync với Zalo                                                     │
│                                                                                  │
│   ✅ CÓ THỂ dùng n8n cho:                                                       │
│   ──────────────────────                                                        │
│   • Background jobs (không cần user interaction)                               │
│   • Scheduled tasks (chạy theo lịch)                                           │
│   • Internal integrations (MISA, Email)                                        │
│   • Data processing pipelines                                                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 n8n Use Cases (Backend)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    n8n BACKEND WORKFLOWS                                         │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ WORKFLOW 1: Daily Report (Scheduled)                                    │   │
│   │                                                                          │   │
│   │  [Cron: 18:00 daily]                                                    │   │
│   │        │                                                                 │   │
│   │        ▼                                                                 │   │
│   │  [Query Database] ──► [Generate Report] ──► [Send Email]               │   │
│   │                                                                          │   │
│   │  • No user interaction needed                                           │   │
│   │  • Runs automatically every day                                         │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ WORKFLOW 2: MISA Sync (Triggered by SLMS)                              │   │
│   │                                                                          │   │
│   │  [SLMS confirms statement]                                              │   │
│   │        │                                                                 │   │
│   │        ▼                                                                 │   │
│   │  [Webhook: /misa-sync] ──► [Map Data] ──► [Call MISA API]              │   │
│   │        │                                                                 │   │
│   │        ▼                                                                 │   │
│   │  [Update SLMS with MISA invoice number]                                 │   │
│   │                                                                          │   │
│   │  • Triggered by SLMS backend (not Zalo)                                │   │
│   │  • Handles MISA integration                                             │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ WORKFLOW 3: Rate Expiry Alert (Scheduled)                              │   │
│   │                                                                          │   │
│   │  [Cron: 08:00 daily]                                                    │   │
│   │        │                                                                 │   │
│   │        ▼                                                                 │   │
│   │  [Check expiring rates] ──► [If found] ──► [Email to Finance]          │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ WORKFLOW 4: Statement Generation (Triggered by SLMS)                   │   │
│   │                                                                          │   │
│   │  [SLMS requests statement generation]                                   │   │
│   │        │                                                                 │   │
│   │        ▼                                                                 │   │
│   │  [Webhook] ──► [Query Jobs] ──► [Generate PDF] ──► [Email to Customer] │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Alternative: No n8n (Pure FastAPI)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    ALTERNATIVE: FASTAPI ONLY (No n8n)                            │
│                                                                                  │
│   Nếu không muốn thêm n8n, có thể dùng FastAPI + Celery/APScheduler:           │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                        FASTAPI BACKEND                                  │   │
│   │                                                                          │   │
│   │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │   │
│   │  │   API Routes     │  │   Background     │  │   Scheduler      │      │   │
│   │  │                  │  │   Tasks (Celery) │  │  (APScheduler)   │      │   │
│   │  │  /api/ai/process │  │                  │  │                  │      │   │
│   │  │  /api/jobs       │  │  • MISA sync     │  │  • Daily report  │      │   │
│   │  │  /api/statements │  │  • Email send    │  │  • Rate expiry   │      │   │
│   │  │                  │  │  • PDF generate  │  │  • AR aging      │      │   │
│   │  └──────────────────┘  └──────────────────┘  └──────────────────┘      │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   Pros:                                                                          │
│   • Simpler architecture (1 service)                                            │
│   • Easier to deploy                                                            │
│   • All code in Python                                                          │
│                                                                                  │
│   Cons:                                                                          │
│   • Need to code workflows manually                                             │
│   • No visual workflow editor                                                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Future Automation Roadmap

### 5.1 Evolution Path

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    AUTOMATION EVOLUTION ROADMAP                                  │
│                                                                                  │
│   PHASE 1: CURRENT (Manual-Assisted)                                            │
│   ══════════════════════════════════                                            │
│                                                                                  │
│   [Zalo] ◄──copy/paste──► [OPS] ◄──► [SLMS UI] ◄──► [AI]                       │
│                                                                                  │
│   • Human copies from Zalo to SLMS                                              │
│   • Human reviews AI output                                                     │
│   • Human copies from SLMS to Zalo                                              │
│   • 100% human control                                                          │
│                                                                                  │
│   ─────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│   PHASE 2: FUTURE (Semi-Automated)                                              │
│   ════════════════════════════════                                              │
│                                                                                  │
│   [Zalo PC] ──screen capture──► [SLMS Desktop App] ──► [AI] ──► [Auto-fill]    │
│                                        │                                        │
│                                   [Human Review]                                │
│                                        │                                        │
│                             [One-click send to Zalo]                           │
│                                                                                  │
│   • Desktop app monitors Zalo window                                           │
│   • Auto-capture new messages                                                  │
│   • AI processes automatically                                                 │
│   • Human reviews and approves                                                 │
│   • One-click to paste back                                                    │
│                                                                                  │
│   ─────────────────────────────────────────────────────────────────────────────│
│                                                                                  │
│   PHASE 3: FAR FUTURE (Full Automation)                                         │
│   ═════════════════════════════════════                                         │
│                                                                                  │
│   [Zalo Official API] ──webhook──► [SLMS] ──► [AI] ──► [Auto-reply]            │
│                                                                                  │
│   • Only if Zalo releases official API                                         │
│   • Still needs human oversight for exceptions                                 │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 SUMMARY

### Current Architecture (Phase 1)
- **No Zalo bot/webhook** - Manual copy/paste
- **SLMS Chat UI** - Central interface for OPS
- **AI Service** - Process input, extract data, generate messages
- **Human-in-the-loop** - Always review before action

### Key Points
1. OPS copy từ Zalo → paste vào SLMS
2. AI xử lý → OPS review → confirm
3. SLMS generate message → OPS copy → paste vào Zalo
4. n8n chỉ dùng cho backend tasks (nếu cần)

### Benefits
- Safe: Human always reviews
- Flexible: Handle edge cases easily
- Simple: No complex integrations
- Fast: AI reduces 80% manual work
