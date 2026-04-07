# AI Chat Bot Architecture & Data Management

## 1. Chat Endpoint & Message Processing

### Main Chat Endpoint
- **File:** `/backend/app/api/chat.py`
- **Route:** `POST /api/chat/message` (with alias `/api/chat/process`)
- **Handler:** `send_message()` in FastAPI router

### Message Flow
1. User sends message via `ChatRequest` model with:
   - `message`: User's text input
   - `session_id`: Optional session identifier (auto-generated if missing)
   - `content_type`: Defaults to "TEXT"
   - `context`: Additional context dict

2. Message processed by **ConversationManager** singleton which:
   - Maintains conversation state per session
   - Loads database context (customers, vendors, active jobs)
   - Sends to unified prompt-based AI processor

3. AI response returns `ChatResponse` with:
   - `response`: AI's reply text
   - `session_id`: Session identifier
   - `needs_confirmation`: Boolean flag if action needs user approval
   - `confirmation_data`: Details for confirmation dialog
   - `task_state`: Current task state
   - `accumulated_entities`: Extracted data so far

### Session Management
- **Store:** `InMemorySessionStore` by default (can be swapped for persistent)
- **Session Endpoints:**
  - `GET /api/chat/session/{session_id}` - Get current state
  - `POST /api/chat/confirm/{session_id}` - Confirm pending action
  - `POST /api/chat/cancel/{session_id}` - Cancel current task
  - `GET /api/chat/debug/sessions` - List all active sessions

---

## 2. AI Bot Tools/Functions (Intents)

The bot uses **intent-based task system** rather than explicit "tools". The AI determines intent and extracts entities.

### Available Intents/Actions

#### A. **create_booking** (Tạo booking/job)
- **Purpose:** Create new logistics job
- **Required Fields:**
  - `customer_code`: Customer identifier
  - `booking_date`: Date of booking
  - `pickup_address` or `origin_address`: Origin location
  - `delivery_address` or `dest_address`: Destination
  - `cargo_type`: Type of goods
  - `package_quantity` + `package_unit`: Quantity info
  - `invoice_numbers`: Billing reference (INV, CD, Bill, CO)
  - `vehicle_type`: Truck type (1.25T, 2.5T, 5T, 10T, etc.)
  - `pickup_time`: Time to pick up cargo

- **Optional Fields:**
  - `vehicles`: Array of vehicle assignments
    ```json
    [
      {
        "license_plate": "29H-81641",
        "vehicle_type": "5T",
        "driver_name": "Nguyễn Văn A",
        "driver_phone": "0912345678",
        "driver_cccd": "123456789"
      }
    ]
    ```
  - `receiver_contact`, `special_requirements`, `notes`

- **Execution:**
  - Calls `POST /api/jobs/create` with extracted entities
  - Optionally assigns vehicles via `POST /api/jobs/{job_id}/assign-vehicle`
  - Returns created job number + vendor-ready dispatch message

#### B. **assign_vehicle** (Gán xe cho job)
- **Purpose:** Assign vehicle(s) to existing job
- **Required Fields:**
  - `job_number`: Existing job identifier (TRK-YYMM-XXX or 3-digit shorthand)
  - `license_plate`: Vehicle plate number
  - `driver_name`: Driver name
  - `driver_phone`: Driver contact
  - `driver_cccd`: Driver ID card

- **Optional Fields:**
  - `vehicle_type`: Type of truck
  - `vendor_code`: Vendor/carrier code
  - Multiple vehicles in `vehicles` array

- **Execution:**
  - Looks up job by `job_number`
  - Calls `POST /api/jobs/{job_id}/assign-vehicle` for each vehicle
  - Returns success message with vendor dispatch info

#### C. **update_status** (Cập nhật trạng thái)
- **Purpose:** Update job status
- **Required Fields:**
  - `job_number`: Which job to update
  - `new_status`: New status code (COMPLETED, IN_TRANSIT, DISPATCHED, CANCELLED, etc.)

- **Optional Fields:**
  - `notes`: Additional notes

- **Execution:**
  - Calls `POST /api/jobs/update` with status change
  - Returns success/failure

#### D. **update_job** (Cập nhật job - combined)
- **Purpose:** Update job with multiple changes (status + cost + revenue)
- **Covers:** Status change + cost addition + revenue addition in one action
- **Execution:** Routes to appropriate handlers based on what's in entities

#### E. **add_cost** (Thêm chi phí)
- **Purpose:** Add cost/expense to job
- **Required Fields:**
  - `job_number`: Which job
  - `cost_name`: Name of cost (e.g., "Xăng", "Bốc xếp", "Hủy chuyến")
  - `cost_unit_price`: Amount
  - `cost_qty`: Quantity
  - `cost_unit`: Unit (ca/trip/CBM/etc.)

#### F. **add_revenue** (Thêm doanh thu)
- **Purpose:** Add revenue to job
- **Same structure as add_cost**
  - `revenue_name`, `revenue_unit_price`, `revenue_qty`, `revenue_unit`

#### G. **add_note** (Thêm ghi chú)
- **Purpose:** Add notes to job
- **Required:** `job_number`, `notes`

#### H. **create_quotation** (Tạo báo giá/rate)
- **Purpose:** Create buying or selling rate/quotation
- **Required Fields:**
  - `quote_type`: "buying" or "selling"
  - `vendor_name` (if buying) or `customer_name` (if selling)
  - `price`: Price amount
  - `vehicle_type` or `origin_province`/`destination_province`
  - `unit`: Unit (TRIP, CBM, KG, etc.)

- **Optional Fields:**
  - `currency`: Currency (defaults to VND)
  - `rate_type`: STANDARD, SPECIAL, etc.
  - `sub_route` or `notes`: Additional info

- **Execution:**
  - Looks up vendor/customer by name from database
  - Creates rate via `POST /api/admin/buying-rates` or `POST /api/admin/selling-rates`

#### I. **create_customer** (Tạo khách hàng)
- **Purpose:** Add new customer

#### J. **create_vendor** (Tạo vendor)
- **Purpose:** Add new vendor/carrier

#### K. **general_query** (Hỏi thông tin)
- **Purpose:** Answer questions, provide information
- **No execution needed** - just conversational response

---

## 3. How Bot Creates Jobs/Assigns Vendors

### Step 1: Intent Recognition
- **File:** `backend/app/ai/unified_processor.py` (lines 73-186)
- **Process:** Unified AI prompt analyzes user message, determines intent
- **Output:** JSON with `intent`, `entities`, `missing_fields`, `ready_to_execute`

### Step 2: Entity Extraction
- **File:** `backend/app/ai/prompts/unified_logistics_prompt.py`
- **Prompt:** System prompt instructs AI to extract:
  - Customer details (code, name, address)
  - Job details (dates, times, cargo type, invoice numbers)
  - Vehicle info (plates, driver names, phone, CCCD)
  - Multiple bookings as `bookings[]` array if user provides multiple shipments
  - Multiple vehicles as `vehicles[]` array if user assigns multiple trucks

### Step 3: Confirmation
- **File:** `backend/app/ai/unified_processor.py` (lines 252-306)
- **Process:** 
  - If ready_to_execute = true (user said "ok"), execution proceeds
  - Otherwise, bot displays confirmation message with all extracted fields
  - User must confirm with "ok", "có", "được", "đồng ý", etc.

### Step 4: Action Execution
- **File:** `backend/app/ai/unified_processor.py` (lines 308-625)
- **For create_booking:**
  1. Calls `POST /api/jobs/create` with entities
  2. If vehicles present, calls `POST /api/jobs/{job_id}/assign-vehicle` for each
  3. Builds vendor-ready dispatch message (copy-friendly format)
  
  **Vendor Message Format:**
  ```
  TRK-2603-001 | INV: INV001
  📦 10 kiện (Điện tử) - Xe 5T
  📅 2026-03-03 - 08:00
  🔵 Lấy: 123 Nguyễn Huệ, TP.HCM
  🔴 Giao: 456 Tây Sơn, Hà Nội
  🚛 Xe: 29H-81641 (5T)
  👤 Tài xế: Nguyễn Văn A - 0912345678 - CCCD: 123456789
  ```

- **For assign_vehicle:**
  1. Looks up job by `job_number` (with smart matching for short codes)
  2. Calls `POST /api/jobs/{job_id}/assign-vehicle` for each vehicle
  3. Fetches job details
  4. Builds vendor message with vehicle info appended

---

## 4. Rate/Quotation Management

### Rate/Quotation Parsing

#### A. From Excel Files
- **File:** `backend/app/api/chat.py` (lines 414-515)
- **Parsers:**
  - `QuotationParser` - For rate sheets with debit/estimate format
  - `BookingFormParser` - For trucking booking forms with multiple shipments
  - Both support auto-detection via `is_quotation_file()` and `is_booking_form()`

#### B. AI-Powered Rate Extraction
- **File:** `backend/app/ai/excel/rate-sheet-ai-parser.py`
- **Process:**
  1. Converts Excel sheet to text representation
  2. Sends to AI (Gemini/DeepSeek/Anthropic) with specific prompt
  3. AI extracts all rate entries from any Excel format
  4. Returns structured rate list: `[{origin, destination, vehicle_type, price, unit, notes}, ...]`

- **Service Type Detection:**
  - TRUCKING_DOM: Domestic trucking (tuyến đường, loại xe)
  - BORDER_IMP: Border import (cửa khẩu, xe TQ, Hữu Nghị)
  - AIR_IMP/AIR_EXP: Air freight
  - SEA_IMP/SEA_EXP: Sea freight
  - PACKING, WAREHOUSE, CUSTOMS: Services (không cần origin/dest)

### Rate Management APIs

#### Buying Rates (Nhà cung cấp)
- `GET /api/admin/buying-rates` - List all buying rates
- `POST /api/admin/buying-rates` - Create buying rate
  ```json
  {
    "vendor_id": 5,
    "price": 1500000,
    "currency": "VND",
    "unit": "TRIP",
    "vehicle_type": "5T",
    "origin_province": "TP.HCM",
    "destination_province": "Hà Nội",
    "notes": "Áp dụng từ 01/03/2026",
    "rate_type": "STANDARD",
    "is_active": true
  }
  ```

#### Selling Rates (Khách hàng)
- `GET /api/admin/selling-rates` - List all selling rates
- `POST /api/admin/selling-rates` - Create selling rate
  ```json
  {
    "customer_id": 10,
    "price": 2000000,
    "currency": "VND",
    "unit": "TRIP",
    "vehicle_type": "5T",
    "origin_province": "TP.HCM",
    "destination_province": "Hà Nội",
    "notes": "Giá ưu đãi",
    "rate_type": "STANDARD",
    "is_active": true
  }
  ```

#### Quotation Search
- `GET /api/jobs/quotations/search` - Find matching quotations based on:
  - `service_type`: TRUCKING_DOM, CUSTOMS, PACKING, etc.
  - `vehicle_type`: 5T, 10T, 20ft, 40ft, etc.
  - `origin_province`: Starting province
  - `destination_province`: Ending province
  - Returns matching rates from buying/selling tables

#### Service Quotation Update
- `PUT /api/jobs/services/{svc_id}/quotations` - Update quotations for a service
  - Merge buying/selling prices with service details
  - Returns updated quotation data

---

## 5. Conversation State & Memory

### Conversation State Structure
- **File:** `backend/app/ai/memory/conversation_state.py`
- **Per-Session Storage:**
  - `session_id`: Unique identifier
  - `intent`: Current detected intent
  - `entities`: Accumulated extracted data
  - `messages`: Chat history (user + assistant)
  - `task_state`: COLLECTING, CONFIRMING, EXECUTING, COMPLETED
  - `missing_fields`: Fields still needed
  - `created_at`, `last_activity`: Timestamps

### Context Loading
- **File:** `backend/app/ai/context_loader.py`
- **Loaded on every message:**
  - Active customers (first 50)
  - Active vendors (first 30)
  - Active jobs (first 20)
  - Current date for parsing
  - Used in unified prompt to help AI match references

---

## 6. File Upload Processing

### Upload Endpoints
1. **POST /api/chat/process-file**
   - Accepts `.xlsx`, `.xls`, `.pdf` files
   - Auto-detects if quotation or booking form
   - Parses and formats content for AI
   - Sends as message to conversation

2. **POST /api/chat/process-image**
   - Accepts image files
   - Uses Google Gemini for OCR
   - Extracts intent, entities, summary
   - Feeds into conversation

### Processing Flow
- Save to temp file
- Detect file type
- Parse with appropriate parser
- Format result into human-readable text with:
  - `[SERVICE_TYPE:TRUCKING_DOM]` marker for AI
  - Customer info, contact details
  - Booking/quotation details
  - Prices and totals
- Send to chat endpoint as regular message

---

## Key Files Summary

| File | Purpose |
|------|---------|
| `backend/app/api/chat.py` | Main chat endpoints |
| `backend/app/ai/memory/conversation_manager.py` | Session management + action execution |
| `backend/app/ai/unified_processor.py` | Intent detection, entity extraction, vendor messaging |
| `backend/app/ai/prompts/unified_logistics_prompt.py` | System prompt template |
| `backend/app/ai/excel/rate-sheet-ai-parser.py` | AI-powered rate extraction from Excel |
| `backend/app/api/jobs.py` | Job creation + quotation search endpoints |
| `backend/app/api/admin.py` | Rate management endpoints |

---

## Notes

- **No Traditional Tools/Function Calls:** Bot doesn't use OpenAI function calling; instead uses unified prompt + intent classification
- **Confirmation Required:** All create/update actions need explicit user confirmation (except for info queries)
- **Multiple Items:** Bot handles batch operations (multiple bookings, multiple vehicles) via arrays
- **Rate Search Integration:** Quotation system integrated into job creation workflow
- **Vendor-Ready Messages:** All created jobs output copy-friendly dispatch messages for vendor communication
