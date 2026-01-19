# 💬 MODULE 2.3: COMMUNICATION (Chat UI Workflow)

## 📋 Mục lục
1. [Communication Flow](#1-communication-flow)
2. [Chat UI Interface](#2-chat-ui-interface)
3. [AI Processing Pipeline](#3-ai-processing-pipeline)
4. [Message Templates](#4-message-templates)
5. [Backend API](#5-backend-api)

---

## 1. Communication Flow

### 1.1 Manual Copy-Paste Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    COMMUNICATION WORKFLOW                                        │
│                                                                                  │
│   Nguyên tắc: SLMS KHÔNG kết nối trực tiếp với Zalo                            │
│   ──────────────────────────────────────────────────                            │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                          │   │
│   │   ZALO                    OPS/CS                    SLMS CHAT UI        │   │
│   │   ────                    ──────                    ─────────────        │   │
│   │                                                                          │   │
│   │   [Customer msg] ──copy──► [OPS] ──paste──► [Input Box]                 │   │
│   │                                                                          │   │
│   │                                              ▼                           │   │
│   │                                        [AI Process]                      │   │
│   │                                              ▼                           │   │
│   │                                        [Review Form]                     │   │
│   │                                              ▼                           │   │
│   │                           ◄──review── [OPS Confirm]                     │   │
│   │                                              ▼                           │   │
│   │                                        [Job Created]                     │   │
│   │                                              ▼                           │   │
│   │   [Vendor group] ◄──paste── [OPS] ◄──copy── [Message Box]              │   │
│   │                                                                          │   │
│   │   [Vendor reply] ──copy──► [OPS] ──paste──► [Input Box]                 │   │
│   │                                              ▼                           │   │
│   │                                        [AI Extract]                      │   │
│   │                                              ▼                           │   │
│   │                           ◄──review── [OPS Confirm]                     │   │
│   │                                              ▼                           │   │
│   │                                        [Vehicle Assigned]                │   │
│   │                                              ▼                           │   │
│   │   [Customer group] ◄──paste── [OPS] ◄──copy── [Message Box]            │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   Lợi ích:                                                                       │
│   ✓ Human-in-the-loop: Luôn có người kiểm tra                                  │
│   ✓ Không cần Zalo API (không có official API cho group)                       │
│   ✓ Linh hoạt xử lý các trường hợp đặc biệt                                   │
│   ✓ An toàn: Không lo bot gửi nhầm                                             │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Communication Channels

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    COMMUNICATION CHANNELS                                        │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📱 ZALO (Primary - Manual)                                              │   │
│   │                                                                          │   │
│   │   Direction   │ Method                  │ Action                        │   │
│   │   ────────────┼─────────────────────────┼──────────────────────────────│   │
│   │   Inbound     │ OPS copy from Zalo      │ Paste to SLMS Chat UI        │   │
│   │   Outbound    │ SLMS generates message  │ OPS copy & paste to Zalo     │   │
│   │                                                                          │   │
│   │   Zalo Groups:                                                          │   │
│   │   • Customer groups: DRT1, DRT2, SEVT, HSDN, DS-BN...                  │   │
│   │   • Vendor groups: Tam Bảo, Việt Thắng, Nam Bình...                    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📧 EMAIL (Secondary - Can be Automated)                                 │   │
│   │                                                                          │   │
│   │   Use cases:                                                            │   │
│   │   • Send statements/invoices to customers                               │   │
│   │   • Send daily reports to management                                    │   │
│   │   • Formal communications                                               │   │
│   │                                                                          │   │
│   │   Can use SMTP automation via FastAPI background tasks                  │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 🔔 IN-APP (Internal Notifications)                                      │   │
│   │                                                                          │   │
│   │   Use cases:                                                            │   │
│   │   • Alert OPS about new pending jobs                                    │   │
│   │   • Notify about rate expiry                                            │   │
│   │   • Remind about unassigned jobs                                        │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Chat UI Interface

### 2.1 Main Chat Interface

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SLMS CHAT UI DESIGN                                      │
│                                                                                  │
│   ╔═════════════════════════════════════════════════════════════════════════╗   │
│   ║  SLMS - AI Assistant                              [Jobs] [Settings] [?] ║   │
│   ╠═════════════════════════════════════════════════════════════════════════╣   │
│   ║                                                                          ║   │
│   ║  ┌─────────────────────────────────────────────────────────────────┐    ║   │
│   ║  │                    CONTEXT SELECTOR                             │    ║   │
│   ║  │                                                                  │    ║   │
│   ║  │  Mode: [● Auto-detect] [ ] Specific Job                        │    ║   │
│   ║  │                                                                  │    ║   │
│   ║  │  Source: [Customer ▼]  Name: [DRT1 - DREAMTECH        ▼]      │    ║   │
│   ║  │                                                                  │    ║   │
│   ║  └─────────────────────────────────────────────────────────────────┘    ║   │
│   ║                                                                          ║   │
│   ║  ┌─────────────────────────────────────────────────────────────────┐    ║   │
│   ║  │                    CONVERSATION AREA                            │    ║   │
│   ║  │                    (Scrollable)                                 │    ║   │
│   ║  │                                                                  │    ║   │
│   ║  │  ┌───────────────────────────────────────────────────────────┐ │    ║   │
│   ║  │  │ 👤 You (21:30)                                            │ │    ║   │
│   ║  │  │ [Pasted text or uploaded file shown here]                 │ │    ║   │
│   ║  │  └───────────────────────────────────────────────────────────┘ │    ║   │
│   ║  │                                                                  │    ║   │
│   ║  │  ┌───────────────────────────────────────────────────────────┐ │    ║   │
│   ║  │  │ 🤖 Assistant (21:30)                                      │ │    ║   │
│   ║  │  │ [AI response with extracted data]                         │ │    ║   │
│   ║  │  │ [Action form or generated message]                        │ │    ║   │
│   ║  │  └───────────────────────────────────────────────────────────┘ │    ║   │
│   ║  │                                                                  │    ║   │
│   ║  └─────────────────────────────────────────────────────────────────┘    ║   │
│   ║                                                                          ║   │
│   ║  ┌─────────────────────────────────────────────────────────────────┐    ║   │
│   ║  │                      INPUT AREA                                 │    ║   │
│   ║  │                                                                  │    ║   │
│   ║  │  ┌───────────────────────────────────────────────────────────┐ │    ║   │
│   ║  │  │                                                            │ │    ║   │
│   ║  │  │  Paste text, drag & drop file, or type here...            │ │    ║   │
│   ║  │  │                                                            │ │    ║   │
│   ║  │  │                                                            │ │    ║   │
│   ║  │  └───────────────────────────────────────────────────────────┘ │    ║   │
│   ║  │                                                                  │    ║   │
│   ║  │  [📷 Image] [📄 File] [📋 Paste]            [🚀 Send to AI]   │    ║   │
│   ║  │                                                                  │    ║   │
│   ║  └─────────────────────────────────────────────────────────────────┘    ║   │
│   ║                                                                          ║   │
│   ╚═════════════════════════════════════════════════════════════════════════╝   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Context Selector Explained

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    CONTEXT SELECTOR                                              │
│                                                                                  │
│   Purpose: Giúp AI hiểu ngữ cảnh để xử lý chính xác hơn                        │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ MODE                                                                    │   │
│   │                                                                          │   │
│   │ [● Auto-detect]                                                         │   │
│   │    AI tự nhận diện:                                                     │   │
│   │    - Đây là booking mới hay vehicle info?                              │   │
│   │    - Từ customer hay vendor?                                           │   │
│   │    - Liên quan đến job nào?                                            │   │
│   │                                                                          │   │
│   │ [ ] Specific Job: [TRK-2601-0089 ▼]                                    │   │
│   │    Khi OPS biết chắc message liên quan đến job cụ thể                  │   │
│   │    Giúp AI matching chính xác hơn                                      │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ SOURCE (Optional but helpful)                                          │   │
│   │                                                                          │   │
│   │ Source: [Customer ▼]                                                   │   │
│   │         ├── Customer (Booking request)                                 │   │
│   │         ├── Vendor (Vehicle info)                                      │   │
│   │         └── Internal (Team communication)                              │   │
│   │                                                                          │   │
│   │ Name: [DRT1 - DREAMTECH ▼]                                             │   │
│   │       Dynamic list based on Source selection                           │   │
│   │       • If Customer: List customers                                    │   │
│   │       • If Vendor: List vendors                                        │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   Khi OPS set context:                                                          │
│   • AI có thêm thông tin để xử lý                                              │
│   • Tự động lookup rates, routes, contacts                                     │
│   • Giảm sai sót trong entity extraction                                       │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Input Types & Preview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    INPUT TYPES & PREVIEW                                         │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📝 TEXT INPUT                                                           │   │
│   │                                                                          │   │
│   │ OPS copy từ Zalo → Ctrl+V vào input box                                │   │
│   │                                                                          │   │
│   │ ┌──────────────────────────────────────────────────────────────────┐   │   │
│   │ │ Ngày mai 22h cần xe 1.25T chở 2 kiện linh kiện từ DRT1          │   │   │
│   │ │ ra Nội Bài. Invoice: 260116DRT-001, 260116DRT-002               │   │   │
│   │ └──────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📄 FILE INPUT (Excel, PDF)                                              │   │
│   │                                                                          │   │
│   │ OPS download file từ Zalo → Drag & drop hoặc click [📄 File]           │   │
│   │                                                                          │   │
│   │ ┌──────────────────────────────────────────────────────────────────┐   │   │
│   │ │ 📄 Phiếu book xe.xlsx                                            │   │   │
│   │ │    Size: 24 KB                                                    │   │   │
│   │ │    [Preview] [Remove]                                             │   │   │
│   │ └──────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   │ Preview shows first few rows of Excel:                                  │   │
│   │ ┌──────────────────────────────────────────────────────────────────┐   │   │
│   │ │ A: Ngày       B: 17/01/2026                                      │   │   │
│   │ │ A: Giờ        B: 22:00                                           │   │   │
│   │ │ A: Invoice    B: 260116DRT-001                                   │   │   │
│   │ │ ...                                                               │   │   │
│   │ └──────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ 📷 IMAGE INPUT (Screenshot)                                             │   │
│   │                                                                          │   │
│   │ OPS chụp màn hình Zalo → Paste hoặc click [📷 Image]                   │   │
│   │                                                                          │   │
│   │ ┌──────────────────────────────────────────────────────────────────┐   │   │
│   │ │                                                                   │   │   │
│   │ │   [Screenshot thumbnail]                                         │   │   │
│   │ │                                                                   │   │   │
│   │ │   📷 screenshot_2026-01-17.png                                   │   │   │
│   │ │   [Preview] [Remove]                                              │   │   │
│   │ │                                                                   │   │   │
│   │ └──────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   │ AI will use Vision model (Gemini) for OCR                              │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. AI Processing Pipeline

### 3.1 Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    AI PROCESSING PIPELINE                                        │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                                                                          │   │
│   │   INPUT                                                                  │   │
│   │   ─────                                                                  │   │
│   │   Text / Excel / Image                                                   │   │
│   │         │                                                                │   │
│   │         ▼                                                                │   │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │   │
│   │   │ STEP 1: CONTENT EXTRACTION                                      │   │   │
│   │   │                                                                  │   │   │
│   │   │ If Text:  → Pass directly                                       │   │   │
│   │   │ If Excel: → Parse with openpyxl/pandas → Structured text       │   │   │
│   │   │ If Image: → Gemini Vision OCR → Extracted text                 │   │   │
│   │   │                                                                  │   │   │
│   │   └───────────────────────────┬─────────────────────────────────────┘   │   │
│   │                               │                                          │   │
│   │                               ▼                                          │   │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │   │
│   │   │ STEP 2: INTENT DETECTION                                        │   │   │
│   │   │                                                                  │   │   │
│   │   │ Model: Gemini 2.0 Flash / DeepSeek                             │   │   │
│   │   │                                                                  │   │   │
│   │   │ Intents:                                                        │   │   │
│   │   │ • CREATE_JOB      - Booking request từ customer                │   │   │
│   │   │ • ASSIGN_VEHICLE  - Vehicle info từ vendor                     │   │   │
│   │   │ • UPDATE_JOB      - Thay đổi thông tin job                     │   │   │
│   │   │ • COMPLETE_JOB    - Xác nhận hoàn thành                        │   │   │
│   │   │ • CANCEL_JOB      - Hủy job                                    │   │   │
│   │   │ • QUERY_STATUS    - Hỏi trạng thái                             │   │   │
│   │   │ • GENERAL_QUERY   - Câu hỏi khác                               │   │   │
│   │   │                                                                  │   │   │
│   │   │ Output: Intent + Confidence (0.0 - 1.0)                        │   │   │
│   │   │                                                                  │   │   │
│   │   └───────────────────────────┬─────────────────────────────────────┘   │   │
│   │                               │                                          │   │
│   │                               ▼                                          │   │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │   │
│   │   │ STEP 3: ENTITY EXTRACTION                                       │   │   │
│   │   │                                                                  │   │   │
│   │   │ Based on Intent, extract relevant entities:                    │   │   │
│   │   │                                                                  │   │   │
│   │   │ CREATE_JOB entities:                                           │   │   │
│   │   │ • customer_code: "DRT1"                                        │   │   │
│   │   │ • booking_date: "2026-01-17"                                   │   │   │
│   │   │ • pickup_time: "22:00"                                         │   │   │
│   │   │ • vehicle_type: "1.25T"                                        │   │   │
│   │   │ • invoice_numbers: ["260116DRT-001", "260116DRT-002"]          │   │   │
│   │   │ • cargo_type: "Linh kiện điện tử"                              │   │   │
│   │   │ • package_info: "2 kiện"                                       │   │   │
│   │   │ • delivery_address: "Sân bay Nội Bài"                          │   │   │
│   │   │                                                                  │   │   │
│   │   │ ASSIGN_VEHICLE entities:                                       │   │   │
│   │   │ • license_plate: "29H 76514"                                   │   │   │
│   │   │ • driver_name: "Nguyễn Việt Đức"                               │   │   │
│   │   │ • driver_phone: "0912345678"                                   │   │   │
│   │   │ • driver_id_card: "001234567890"                               │   │   │
│   │   │                                                                  │   │   │
│   │   └───────────────────────────┬─────────────────────────────────────┘   │   │
│   │                               │                                          │   │
│   │                               ▼                                          │   │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │   │
│   │   │ STEP 4: DATA ENRICHMENT                                         │   │   │
│   │   │                                                                  │   │   │
│   │   │ Lookup from database:                                           │   │   │
│   │   │ • customer_code → customer_id, customer_name, addresses        │   │   │
│   │   │ • route detection → route_id, pickup_address, delivery_address │   │   │
│   │   │ • rate lookup → cost_amount, revenue_amount, margin            │   │   │
│   │   │ • pending jobs → match vehicle info to correct job             │   │   │
│   │   │                                                                  │   │   │
│   │   └───────────────────────────┬─────────────────────────────────────┘   │   │
│   │                               │                                          │   │
│   │                               ▼                                          │   │
│   │   ┌─────────────────────────────────────────────────────────────────┐   │   │
│   │   │ STEP 5: RESPONSE GENERATION                                     │   │   │
│   │   │                                                                  │   │   │
│   │   │ Generate:                                                       │   │   │
│   │   │ • Summary of extracted data                                    │   │   │
│   │   │ • Pre-filled form for review                                   │   │   │
│   │   │ • Suggested action                                             │   │   │
│   │   │                                                                  │   │   │
│   │   └─────────────────────────────────────────────────────────────────┘   │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 AI Model Configuration

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    AI MODEL CONFIGURATION                                        │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ PRIMARY MODEL: GEMINI 2.0 FLASH                                        │   │
│   │                                                                          │   │
│   │ Model ID: gemini-2.0-flash-exp                                         │   │
│   │ Use cases: Intent detection, Entity extraction, Text generation        │   │
│   │ Cost: ~$0.075 / 1M tokens                                              │   │
│   │                                                                          │   │
│   │ Pros:                                                                   │   │
│   │ • Very cost effective                                                  │   │
│   │ • Fast response time                                                   │   │
│   │ • Good Vietnamese language support                                     │   │
│   │ • Multimodal (text + vision)                                          │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ ALTERNATIVE: DEEPSEEK                                                   │   │
│   │                                                                          │   │
│   │ Model ID: deepseek-chat                                                │   │
│   │ Use cases: Backup for Gemini, Complex reasoning                        │   │
│   │ Cost: ~$0.14 / 1M input, $0.28 / 1M output                            │   │
│   │                                                                          │   │
│   │ Pros:                                                                   │   │
│   │ • Very competitive pricing                                             │   │
│   │ • Strong reasoning capabilities                                        │   │
│   │ • Good for structured output                                           │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ VISION MODEL: GEMINI VISION                                            │   │
│   │                                                                          │   │
│   │ Use cases: OCR from screenshots                                        │   │
│   │ When: Image input detected                                             │   │
│   │                                                                          │   │
│   │ Flow: Image → Gemini Vision → Extracted Text → Normal NLP pipeline    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   Monthly Cost Estimate:                                                        │
│   ───────────────────────                                                       │
│   • ~100-200 requests/day                                                      │
│   • ~1000 tokens/request average                                               │
│   • Monthly: 3M-6M tokens                                                      │
│   • Cost: $5-15/month with Gemini                                              │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Message Templates

### 4.1 Vendor Templates

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    VENDOR MESSAGE TEMPLATES                                      │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ TEMPLATE: VENDOR_DISPATCH_REQUEST                                       │   │
│   │                                                                          │   │
│   │ Trigger: Job created, vendor selected                                   │   │
│   │ Purpose: Request vehicle/driver from vendor                             │   │
│   │                                                                          │   │
│   │ ───────────────────────────────────────────────────────────────────────│   │
│   │                                                                          │   │
│   │ 🚛 YÊU CẦU XE - {customer_code}                                        │   │
│   │                                                                          │   │
│   │ 📅 Ngày: {booking_date}                                                 │   │
│   │ ⏰ Giờ: {pickup_time}                                                   │   │
│   │ 📦 Invoice: {invoice_numbers}                                           │   │
│   │ 📋 Hàng: {cargo_type} - {package_info}                                 │   │
│   │ 🚗 Loại xe: {vehicle_type}                                             │   │
│   │ 📍 Lấy: {pickup_address}                                               │   │
│   │ 📍 Giao: {delivery_address}                                            │   │
│   │                                                                          │   │
│   │ Vui lòng điều xe và phản hồi thông tin lái xe.                         │   │
│   │                                                                          │   │
│   │ ───────────────────────────────────────────────────────────────────────│   │
│   │                                                                          │   │
│   │ Variables:                                                              │   │
│   │ • customer_code: From job.customer_code                                │   │
│   │ • booking_date: Format dd/mm/yyyy                                      │   │
│   │ • pickup_time: Format HH:mm                                            │   │
│   │ • invoice_numbers: Comma separated                                     │   │
│   │ • cargo_type, package_info: From job                                   │   │
│   │ • vehicle_type: From job                                               │   │
│   │ • pickup_address, delivery_address: From job or route                  │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Customer Templates

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    CUSTOMER MESSAGE TEMPLATES                                    │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ TEMPLATE: CUSTOMER_VEHICLE_CONFIRM                                      │   │
│   │                                                                          │   │
│   │ Trigger: Vehicle assigned to job                                        │   │
│   │ Purpose: Confirm vehicle details to customer                            │   │
│   │                                                                          │   │
│   │ ───────────────────────────────────────────────────────────────────────│   │
│   │                                                                          │   │
│   │ {route_code} / {date} / {time} / Invoice: {invoices} / {cargo}         │   │
│   │ / {package} / {vehicle_type} / BKS: {license_plate} / {driver_name}    │   │
│   │ - {driver_phone} - CCCD: {driver_id_card}                              │   │
│   │                                                                          │   │
│   │ ───────────────────────────────────────────────────────────────────────│   │
│   │                                                                          │   │
│   │ Example output:                                                         │   │
│   │ MK-DRT1 / 17.01 / 22:00 / Invoice: 260116DRT-001, 260116DRT-002 /     │   │
│   │ Linh kiện điện tử / 2 kiện / 1.25T / BKS: 29H 76514 / Nguyễn Việt Đức │   │
│   │ - 0912.345.678 - CCCD: 001234567890                                    │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │ TEMPLATE: CUSTOMER_DELIVERY_CONFIRM                                     │   │
│   │                                                                          │   │
│   │ Trigger: Job completed                                                  │   │
│   │ Purpose: Confirm delivery to customer (optional)                        │   │
│   │                                                                          │   │
│   │ ───────────────────────────────────────────────────────────────────────│   │
│   │                                                                          │   │
│   │ ✅ Đã giao hàng thành công                                              │   │
│   │                                                                          │   │
│   │ Job: {job_number}                                                       │   │
│   │ Invoice: {invoices}                                                     │   │
│   │ Thời gian giao: {delivery_time}                                        │   │
│   │                                                                          │   │
│   │ Cảm ơn quý khách!                                                      │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Backend API

### 5.1 Chat API Endpoints

```python
# chat_api.py - FastAPI endpoints for Chat UI

from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, List
import json

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    content: str
    content_type: str = "TEXT"  # TEXT, FILE, IMAGE
    context: Optional[dict] = None
    # context = {
    #     "source_type": "CUSTOMER" | "VENDOR",
    #     "source_id": "DRT1",
    #     "job_id": 123  # if specific job context
    # }


class ChatResponse(BaseModel):
    intent: str
    confidence: float
    entities: dict
    enriched_data: dict
    suggested_action: str
    form_data: Optional[dict] = None
    generated_message: Optional[str] = None


@router.post("/process", response_model=ChatResponse)
async def process_chat_message(request: ChatRequest):
    """
    Main endpoint for Chat UI
    Process text input and return AI analysis
    """
    
    # Step 1: Get AI service
    ai_service = get_ai_service()
    
    # Step 2: Process with AI
    result = await ai_service.process(
        content=request.content,
        content_type=request.content_type,
        context=request.context
    )
    
    # Step 3: Enrich with database lookups
    enriched = await enrich_entities(result.entities)
    
    # Step 4: Generate form data for review
    form_data = generate_form_data(result.intent, enriched)
    
    return ChatResponse(
        intent=result.intent,
        confidence=result.confidence,
        entities=result.entities,
        enriched_data=enriched,
        suggested_action=get_suggested_action(result.intent),
        form_data=form_data
    )


@router.post("/process-file")
async def process_file(
    file: UploadFile = File(...),
    context: str = Form(default="{}")
):
    """
    Process uploaded Excel/PDF file
    """
    context_dict = json.loads(context)
    
    # Detect file type
    if file.filename.endswith(('.xlsx', '.xls')):
        content = await parse_excel_file(file)
        content_type = "EXCEL"
    elif file.filename.endswith('.pdf'):
        content = await parse_pdf_file(file)
        content_type = "PDF"
    else:
        raise HTTPException(400, "Unsupported file type")
    
    # Process extracted content
    return await process_chat_message(ChatRequest(
        content=content,
        content_type=content_type,
        context=context_dict
    ))


@router.post("/process-image")
async def process_image(
    image: UploadFile = File(...),
    context: str = Form(default="{}")
):
    """
    Process uploaded image (screenshot)
    Uses Gemini Vision for OCR
    """
    context_dict = json.loads(context)
    
    # OCR with Gemini Vision
    image_bytes = await image.read()
    extracted_text = await gemini_vision_ocr(image_bytes)
    
    # Process extracted text
    return await process_chat_message(ChatRequest(
        content=extracted_text,
        content_type="IMAGE_OCR",
        context=context_dict
    ))
```

### 5.2 Action Endpoints

```python
# actions_api.py - Endpoints for executing actions after review

@router.post("/actions/create-job")
async def create_job_from_chat(
    form_data: JobCreateForm,
    current_user: User = Depends(get_current_user)
):
    """
    Create job after OPS reviews and confirms
    Returns created job + generated vendor message
    """
    
    # Create job
    job = await job_service.create(form_data, current_user.id)
    
    # Generate vendor message
    vendor_message = await generate_message(
        template="VENDOR_DISPATCH_REQUEST",
        job=job
    )
    
    # Log to chat session
    await log_chat_action(
        action_type="CREATE_JOB",
        job_id=job.id,
        user_id=current_user.id
    )
    
    return {
        "success": True,
        "job": job,
        "message_for_vendor": vendor_message,
        "copy_instruction": f"Copy tin nhắn và paste vào Zalo group {job.vendor.vendor_name}"
    }


@router.post("/actions/assign-vehicle")
async def assign_vehicle_from_chat(
    job_id: int,
    form_data: VehicleAssignForm,
    current_user: User = Depends(get_current_user)
):
    """
    Assign vehicle after OPS reviews vendor response
    Returns updated job + generated customer message
    """
    
    # Update job
    job = await job_service.assign_vehicle(job_id, form_data, current_user.id)
    
    # Generate customer message
    customer_message = await generate_message(
        template="CUSTOMER_VEHICLE_CONFIRM",
        job=job
    )
    
    return {
        "success": True,
        "job": job,
        "message_for_customer": customer_message,
        "copy_instruction": f"Copy tin nhắn và paste vào Zalo group {job.customer.customer_code}"
    }


@router.post("/actions/complete-job")
async def complete_job_from_chat(
    job_id: int,
    delivery_time: Optional[datetime] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Complete job
    """
    
    job = await job_service.complete(job_id, delivery_time, current_user.id)
    
    return {
        "success": True,
        "job": job,
        "financial_summary": {
            "cost": job.cost_amount,
            "revenue": job.revenue_amount,
            "profit": job.profit_amount,
            "margin": job.profit_amount / job.cost_amount * 100 if job.cost_amount else 0
        }
    }
```

---

## 📊 SUMMARY

### Communication Principle
- **No Zalo API integration** - Manual copy/paste
- **Chat UI is central** - All inputs through SLMS web interface
- **Human-in-the-loop** - OPS reviews before every action

### Input Types
1. **Text** - Copy from Zalo, paste to chat
2. **Excel** - Upload booking file
3. **Image** - Screenshot for OCR

### AI Pipeline
1. Content extraction (text/OCR)
2. Intent detection
3. Entity extraction
4. Data enrichment
5. Response generation

### Message Templates
- `VENDOR_DISPATCH_REQUEST` - Request vehicle
- `CUSTOMER_VEHICLE_CONFIRM` - Confirm details

### API Endpoints
- `POST /api/chat/process` - Main chat processing
- `POST /api/chat/process-file` - Excel/PDF
- `POST /api/chat/process-image` - Screenshot OCR
- `POST /api/chat/actions/*` - Execute confirmed actions
