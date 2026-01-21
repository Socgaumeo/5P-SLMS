# 🧠 SLMS AI Pipeline Module
## Multi-Stage AI Processing for Smart Logistics

**Version:** 1.0.0  
**Date:** 19/01/2026  
**Author:** 5P Vietnam

---

## 📋 GIỚI THIỆU

Module AI Pipeline cung cấp khả năng xử lý ngôn ngữ tự nhiên linh hoạt cho SLMS Chat UI.

### Vấn đề giải quyết:
- ❌ Prompt cứng, chỉ hiểu 1 format cố định
- ❌ User nhập khác format → AI không hiểu
- ❌ Không có conversation context

### Giải pháp:
- ✅ Multi-stage pipeline tự động phân loại intent
- ✅ Few-shot learning với nhiều ví dụ
- ✅ Context-aware extraction từ database
- ✅ Smart fallback với clarification

---

## 🏗️ KIẾN TRÚC

```
User Input (text/image/excel)
       │
       ▼
┌─────────────────────────────────────┐
│ Stage 1: PREPROCESSOR               │
│ Convert to text (OCR, Excel parse)  │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Stage 2: INTENT CLASSIFIER          │
│ Phân loại: booking/vehicle/status   │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Stage 3: CONTEXT LOADER             │
│ Load customers, jobs từ database    │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Stage 4: ENTITY EXTRACTOR           │
│ Extract với few-shot examples       │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│ Stage 5: VALIDATOR                  │
│ Validate & identify missing fields  │
└─────────────────────────────────────┘
       │
       ▼
Output: {intent, entities, confidence, action}
```

---

## 📁 CẤU TRÚC FILES

```
backend/app/ai/
├── __init__.py              # Module exports
├── pipeline.py              # Main orchestrator
├── preprocessor.py          # Stage 1: Text/Image/Excel
├── intent_classifier.py     # Stage 2: Intent classification
├── context_loader.py        # Stage 3: Load from DB
├── entity_extractor.py      # Stage 4: Extract entities
├── validator.py             # Stage 5: Validate
└── prompts/
    ├── __init__.py
    ├── intent_prompts.py    # Intent classification prompt
    ├── booking_prompts.py   # Booking extraction prompt
    ├── vehicle_prompts.py   # Vehicle extraction prompt
    └── status_prompts.py    # Status extraction prompt

SQL/
└── add_chat_sessions.sql    # Database migration

INTEGRATION_GUIDE.md         # Hướng dẫn tích hợp chi tiết
```

---

## 🚀 QUICK START

### 1. Copy files vào project

```bash
cp -r backend/app/ai/ /path/to/your/project/backend/app/
```

### 2. Cài dependencies

```bash
pip install pydantic pandas
```

### 3. Sử dụng

```python
from app.ai import AIPipeline, PipelineInput, InputType

# Initialize
pipeline = AIPipeline(db_session, ai_client)

# Process text
result = await pipeline.process(PipelineInput(
    content="Ngày mai 22h cần xe 1.25T cho DRT1",
    input_type=InputType.TEXT
))

# Result
print(result.intent)        # "create_booking"
print(result.confidence)    # 0.95
print(result.entities)      # {"customer_code": "DRT1", "booking_date": "2026-01-20", ...}
print(result.suggested_action)  # "show_form"
```

---

## 🎯 SUPPORTED INTENTS

| Intent | Mô tả | Ví dụ |
|--------|-------|-------|
| `create_booking` | Tạo job mới | "Ngày mai 22h cần xe 1.25T cho DRT1" |
| `assign_vehicle` | Điều xe | "BKS 29H 76514 - Nguyễn Văn A - 0912345678" |
| `update_status` | Cập nhật trạng thái | "Job TRK-2601-089 đã giao xong" |
| `query_info` | Hỏi thông tin | "Status job 089?" |
| `general_chat` | Chat thông thường | "Cảm ơn anh" |

---

## 📊 CONFIDENCE THRESHOLDS

| Confidence | Action | Mô tả |
|------------|--------|-------|
| ≥ 0.85 | `show_form` | Hiển thị form với dữ liệu đã extract |
| 0.65 - 0.85 | `show_form_uncertain` | Hiển thị form với warnings |
| 0.40 - 0.65 | `ask_clarification` | Hỏi clarification |
| < 0.40 | `cannot_understand` | Không hiểu, show suggestions |

---

## 📖 CHI TIẾT

Xem `INTEGRATION_GUIDE.md` để biết cách tích hợp chi tiết vào project.

---

## 💰 CHI PHÍ ƯỚC TÍNH

Với Gemini 2.0 Flash:
- **~$4/tháng** cho 60 jobs/ngày
- **~$0.07/job** (bao gồm intent + extraction)

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề, kiểm tra:
1. AI Client hoạt động (có API key)
2. Database có dữ liệu customers, routes
3. Xem logs để debug từng stage
