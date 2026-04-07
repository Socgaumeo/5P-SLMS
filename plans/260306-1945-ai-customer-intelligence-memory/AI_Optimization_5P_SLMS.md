# 🤖 Phân Tích & Đề Xuất Tối Ưu AI — 5P-SLMS

> Dựa trên cấu trúc repo `Socgaumeo/5P-SLMS` + tài liệu thiết kế Flexible Excel Parser

---

## 1. BỨC TRANH HIỆN TẠI

### 1.1 Kiến trúc AI hiện có

```
┌─────────────────────────────────────────────────────────┐
│                    AI USAGE MAP (HIỆN TẠI)               │
│                                                          │
│  Chat Interface ──► Entity Extraction ──► Job Creation   │
│       │                                                  │
│  Excel Upload  ──► Schema Detection  ──► Data Import     │
│       │                                                  │
│  Rate Files    ──► Document Parsing  ──► Quotation Gen   │
│                                                          │
│  Stack: Gemini + DeepSeek + Claude API                   │
│  Orchestration: n8n workflows                            │
│  Backend: FastAPI + Supabase                             │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Các điểm yếu đang tồn tại

| Vấn đề | Biểu hiện | Tác động |
|--------|-----------|----------|
| **Gọi AI không phân loại** | Mọi task đều dùng cùng model | Chi phí cao, latency không cần thiết |
| **Không có caching** | Prompt tương tự gọi lại full API | Tốn token cho context lặp lại |
| **JSON parsing fragile** | Multiple fallback strategies | Instability, debug khó |
| **Context window bloat** | Truyền toàn bộ DB data vào prompt | Token waste, độ chính xác giảm |
| **No conversation memory** | Mỗi turn là stateless | User phải repeat info |
| **Single-stage processing** | 1 AI call = 1 task phức tạp | Accuracy thấp với multi-step logic |

---

## 2. CHIẾN LƯỢC TỐI ƯU AI — 5 LỚP

### 🔵 LỚP 1: Model Routing — Dùng đúng model cho đúng task

```
┌────────────────────────────────────────────────────────────────┐
│                    MODEL ROUTING STRATEGY                       │
│                                                                │
│  TASK COMPLEXITY                    MODEL ĐỀ XUẤT             │
│  ──────────────────────────────     ─────────────────────────  │
│                                                                │
│  🟢 Simple (classification,         DeepSeek-v3 / Gemini Flash │
│     extraction, yes/no,             ~$0.1/M tokens            │
│     date parsing)                                              │
│                                                                │
│  🟡 Medium (schema detection,       Claude Sonnet / Gemini Pro │
│     multi-field extraction,         ~$3/M tokens              │
│     customer matching)                                         │
│                                                                │
│  🔴 Complex (quotation analysis,    Claude Opus / Gemini Ultra │
│     multi-doc reconciliation,       ~$15/M tokens             │
│     financial review)                                          │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Ước tính tiết kiệm: 60-75% chi phí AI**

```python
# backend/app/ai/router.py — IMPLEMENT THIS

class AITaskRouter:
    ROUTING_RULES = {
        # Simple tasks → cheap model
        "date_parse": ("deepseek", "deepseek-chat"),
        "intent_classify": ("deepseek", "deepseek-chat"),
        "field_extract_simple": ("gemini", "gemini-1.5-flash"),
        
        # Medium tasks → balanced model
        "schema_detect": ("claude", "claude-haiku-4-5-20251001"),
        "customer_match": ("gemini", "gemini-1.5-pro"),
        "excel_parse": ("claude", "claude-haiku-4-5-20251001"),
        
        # Complex tasks → powerful model
        "quotation_analysis": ("claude", "claude-sonnet-4-6"),
        "multi_doc_reconcile": ("claude", "claude-sonnet-4-6"),
        "financial_audit": ("claude", "claude-opus-4-6"),
    }
    
    async def route(self, task_type: str, payload: dict):
        provider, model = self.ROUTING_RULES.get(task_type, ("claude", "claude-haiku-4-5-20251001"))
        client = self.get_client(provider, model)
        return await client.generate(payload)
```

---

### 🔵 LỚP 2: Prompt Caching — Tiết kiệm 70-95% token cho context tĩnh

Hệ thống SLMS có nhiều **context cố định** lặp đi lặp lại trong mỗi request — đây là cơ hội lớn nhất để tối ưu.

#### Những gì NÊN cache:

```
┌─────────────────────────────────────────────────────────┐
│              CACHEABLE CONTEXT IN SLMS                   │
│                                                          │
│  1. FIELD DEFINITIONS (schema_detector)                  │
│     → Danh sách 13 standard logistics fields             │
│     → Aliases cho từng field                             │
│     → ~2,000 tokens, dùng trong MỌI Excel parse call    │
│                                                          │
│  2. CUSTOMER MASTER DATA                                 │
│     → Danh sách customers + codes + aliases              │
│     → ~1,000-5,000 tokens tùy số lượng KH               │
│     → Cache theo session/user                            │
│                                                          │
│  3. VEHICLE TYPE CATALOG                                 │
│     → Bảng loại xe + aliases VN/EN                       │
│     → ~500 tokens, dùng trong mọi booking parse          │
│                                                          │
│  4. SYSTEM PROMPTS                                       │
│     → Logistics context, business rules                  │
│     → ~1,500 tokens per service                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### Implementation với Claude Prompt Caching:

```python
# Thêm cache_control vào system prompt tĩnh
# backend/app/ai/cached_prompts.py

LOGISTICS_SYSTEM_PROMPT = {
    "type": "text",
    "text": """Bạn là AI assistant cho hệ thống logistics 5P Vietnam.
    
DANH SÁCH KHÁCH HÀNG:
{customer_list}

DANH SÁCH LOẠI XE:
{vehicle_types}

STANDARD FIELDS:
{field_definitions}

BUSINESS RULES:
- Ngày pickup phải trong tương lai
- Container 20FT tối đa 25 tấn
- ...
""",
    "cache_control": {"type": "ephemeral"}  # ← Cache điều này!
}

# Dynamic part (không cache) — chỉ là user data thực tế
USER_CONTENT = {
    "type": "text", 
    "text": "Parse this Excel row: {row_data}"
}
```

**Ước tính tiết kiệm: 70-95% token cost cho Excel parsing operations**

---

### 🔵 LỚP 3: Structured Output Pipeline — Loại bỏ JSON parsing fragility

Thay vì dùng regex để extract JSON từ text response, ép AI trả về **chỉ JSON** với schema cố định.

#### Vấn đề hiện tại:
```python
# Hiện tại — dễ fail
json_match = re.search(r'\{[\s\S]*\}', response)
if json_match:
    result = json.loads(json_match.group())  # ← Fragile!
```

#### Giải pháp đề xuất — 3 lớp validation:

```python
# backend/app/ai/structured_output.py

from pydantic import BaseModel, field_validator
from typing import List, Optional
import json

class FieldMappingOutput(BaseModel):
    excel_column: str
    standard_field: str
    confidence: float
    detected_format: Optional[str] = None
    
    @field_validator('confidence')
    def validate_confidence(cls, v):
        return max(0.0, min(1.0, v))
    
    @field_validator('standard_field')
    def validate_field(cls, v):
        VALID_FIELDS = {'date', 'time', 'customer_code', 'vehicle_type', 
                        'origin', 'destination', 'cargo', 'quantity', 
                        'weight', 'invoice_number', 'notes', 'po_number', 'route'}
        if v not in VALID_FIELDS and v != 'unmapped':
            return 'unmapped'
        return v

class SchemaDetectionOutput(BaseModel):
    mappings: List[FieldMappingOutput]
    format_type: str  # table | form | mixed
    confidence_overall: float

# Prompt engineering cho structured output
SCHEMA_DETECTION_PROMPT = """
Analyze Excel headers and return ONLY valid JSON matching this schema:
{
  "mappings": [...],
  "format_type": "table|form|mixed",
  "confidence_overall": 0.0-1.0
}

NO explanations, NO markdown, ONLY JSON.
"""

async def safe_structured_call(prompt: str, output_model: BaseModel, client, max_retries=3):
    """Gọi AI với retry + Pydantic validation"""
    for attempt in range(max_retries):
        try:
            response = await client.generate(prompt, temperature=0.0)
            # Strip markdown nếu có
            clean = response.strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(clean)
            return output_model(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            if attempt == max_retries - 1:
                raise
            # Retry với prompt clarification
            prompt += f"\n\nPrevious response was invalid: {str(e)[:100]}. Return ONLY JSON."
```

---

### 🔵 LỚP 4: Semantic Caching — Tránh gọi AI cho input tương tự

Nhiều customers gửi Excel format giống nhau mỗi tuần. Schema detection không cần chạy lại.

```
┌─────────────────────────────────────────────────────────┐
│              SEMANTIC CACHE STRATEGY                     │
│                                                          │
│  Input: Excel headers ["Ngày", "Giờ", "KH", "Xe", "Đến"]│
│                                                          │
│  1. Hash headers + sample_data_signature                 │
│  2. Check Supabase cache table                           │
│  3. Cache HIT → Return cached SchemaMapping instantly    │
│  4. Cache MISS → Call AI → Store result                  │
│                                                          │
│  Cache table: excel_schema_cache                         │
│  ┌──────────────────┬────────────┬───────────────────┐  │
│  │ headers_hash     │ schema_json│ hit_count │ ttl   │  │
│  │ sha256(headers)  │ {mappings} │ 47        │ 30d   │  │
│  └──────────────────┴────────────┴───────────────────┘  │
│                                                          │
│  Ước tính: 80% cache hit rate sau 2 tuần               │
└─────────────────────────────────────────────────────────┘
```

```python
# backend/app/ai/excel/schema_cache.py

import hashlib, json
from app.db.session import get_db

class SchemaCache:
    TABLE = "excel_schema_cache"
    TTL_DAYS = 30
    
    def _make_key(self, headers: list, sample_rows: list) -> str:
        # Hash headers + first row structure (not values)
        signature = headers + [type(v).__name__ for v in (sample_rows[0] if sample_rows else [])]
        return hashlib.sha256(json.dumps(signature, sort_keys=True).encode()).hexdigest()
    
    async def get(self, headers, sample_rows) -> Optional[SchemaMapping]:
        key = self._make_key(headers, sample_rows)
        result = await self.db.table(self.TABLE).select("*").eq("headers_hash", key).execute()
        if result.data:
            await self.db.table(self.TABLE).update({"hit_count": result.data[0]["hit_count"] + 1}).eq("headers_hash", key).execute()
            return SchemaMapping(**json.loads(result.data[0]["schema_json"]))
        return None
    
    async def set(self, headers, sample_rows, schema: SchemaMapping):
        key = self._make_key(headers, sample_rows)
        await self.db.table(self.TABLE).upsert({
            "headers_hash": key,
            "schema_json": json.dumps(schema.__dict__),
            "headers_preview": str(headers[:5]),
            "hit_count": 0
        }).execute()
```

---

### 🔵 LỚP 5: Multi-Agent Architecture — Phân chia trách nhiệm AI

Thay vì 1 AI call làm nhiều việc, dùng **pipeline agent chuyên biệt**:

```
┌─────────────────────────────────────────────────────────────────┐
│              MULTI-AGENT PIPELINE (ĐỀ XUẤT)                     │
│                                                                  │
│  User Input (Chat / Excel / File)                                │
│        │                                                         │
│        ▼                                                         │
│  ┌──────────────┐                                                │
│  │  TRIAGE      │  → "Đây là gì?" (classification, Flash model) │
│  │  AGENT       │  → intent: booking | quotation | report       │
│  └──────┬───────┘                                                │
│         │                                                        │
│    ┌────┴────────┬────────────────┐                             │
│    ▼             ▼                ▼                              │
│  ┌──────┐   ┌────────┐   ┌────────────┐                        │
│  │BOOK- │   │QUOTE   │   │REPORT      │                        │
│  │ING   │   │AGENT   │   │AGENT       │                        │
│  │AGENT │   │        │   │            │                        │
│  └──┬───┘   └───┬────┘   └─────┬──────┘                       │
│     │           │              │                                 │
│     ▼           ▼              ▼                                 │
│  ┌──────────────────────────────────────┐                       │
│  │         ENTITY RESOLUTION AGENT      │                       │
│  │  customer_id? vehicle_type_id? route?│                       │
│  │  (Haiku model + DB lookup)           │                       │
│  └──────────────┬───────────────────────┘                       │
│                 │                                                │
│                 ▼                                                │
│  ┌──────────────────────────────────────┐                       │
│  │         VALIDATION AGENT             │                       │
│  │  Business rules check                │                       │
│  │  Confidence threshold                │                       │
│  │  Human-in-loop trigger               │                       │
│  └──────────────────────────────────────┘                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. QUICK WINS — Làm ngay, ROI cao nhất

### Priority 1: Structured Output (1-2 ngày, giảm ~90% parsing errors)

```python
# Thêm vào schema_detector.py — thay toàn bộ json parsing hiện tại

SYSTEM_PROMPT = """Return ONLY valid JSON. No markdown. No explanation.
Schema: {"mappings": [{"excel_column": str, "standard_field": str, "confidence": float}]}"""

# Temperature = 0 cho deterministic output
response = await ai_client.generate(prompt, temperature=0.0)
```

### Priority 2: Model Routing cho Excel Parser (1 ngày, giảm ~60% cost)

```python
# schema_detector.py — thay Claude Opus/Sonnet bằng Haiku cho simple mapping
# Chỉ leo thang lên Sonnet khi confidence < 0.6 từ Haiku

async def detect(self, headers, sample_rows, context=None):
    # Try Haiku first (fast + cheap)
    result = await self._detect_with_model(headers, sample_rows, model="haiku")
    
    if result.overall_confidence < 0.7:
        # Escalate to Sonnet for uncertain cases
        result = await self._detect_with_model(headers, sample_rows, model="sonnet")
    
    return result
```

### Priority 3: Cache System Prompt (nửa ngày, tiết kiệm 70% token)

Bật Claude Prompt Caching cho `STANDARD_FIELDS` definitions và customer list — đây là context gần như không đổi nhưng được gửi lại MỌI request Excel parse.

---

## 4. ROADMAP TÍCH HỢP

```
┌─────────────────────────────────────────────────────────┐
│                    AI OPTIMIZATION ROADMAP               │
│                                                          │
│  TUẦN 1: Nền tảng                                        │
│  ─────────────────────────────────────────────────────  │
│  ✓ Structured Output với Pydantic validation             │
│  ✓ Temperature=0 cho tất cả extraction tasks             │
│  ✓ Model Routing cơ bản (Haiku/Sonnet/Opus)             │
│                                                          │
│  TUẦN 2: Caching                                         │
│  ─────────────────────────────────────────────────────  │
│  ✓ Prompt Caching cho static context                     │
│  ✓ Schema Cache table trong Supabase                     │
│  ✓ Session-level customer list caching                   │
│                                                          │
│  TUẦN 3: Multi-Agent Pipeline                            │
│  ─────────────────────────────────────────────────────  │
│  ✓ Triage Agent (intent classification)                  │
│  ✓ Booking Agent vs Quotation Agent split                │
│  ✓ Entity Resolution Agent với DB lookup                 │
│                                                          │
│  TUẦN 4: Monitoring & Feedback                           │
│  ─────────────────────────────────────────────────────  │
│  ✓ Token usage tracking per task type                    │
│  ✓ Confidence score dashboard                            │
│  ✓ Human correction → auto-improve pipeline              │
└─────────────────────────────────────────────────────────┘
```

---

## 5. TỐI ƯU RIÊNG CHO FLEXIBLE EXCEL PARSER

Dựa trên thiết kế trong `GIAI_PHAP_2_FLEXIBLE_EXCEL_PARSER.md`, đây là 4 cải tiến cụ thể:

### 5.1 Two-Phase Schema Detection

```python
# Phase 1: Rule-based (0ms, free) → xử lý 70% cases
# Phase 2: AI (200-500ms, có phí) → chỉ cho 30% uncertain

async def detect(self, headers, sample_rows):
    # Phase 1: Rule-based
    rule_mappings = self._rule_based_mapping(headers)
    uncertain = [m for m in rule_mappings if m.confidence < 0.85]
    
    if not uncertain:
        return self._build_schema(rule_mappings)  # ← Return ngay, không gọi AI
    
    # Phase 2: AI chỉ cho uncertain columns
    ai_mappings = await self._ai_mapping_batch(
        uncertain_headers=[m.excel_column for m in uncertain],
        sample_rows=sample_rows[:3],
        model="claude-haiku-4-5-20251001"  # Haiku đủ dùng cho column mapping
    )
    
    return self._merge_and_build(rule_mappings, ai_mappings)
```

### 5.2 Batch Processing cho nhiều Excel rows

```python
# Thay vì normalize từng row một, batch 10 rows mỗi call

async def extract_batch(self, rows: List[List], schema: SchemaMapping, batch_size=10):
    results = []
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        # 1 AI call cho 10 rows thay vì 10 calls
        normalized = await self._batch_normalize(batch, schema)
        results.extend(normalized)
    return results
```

### 5.3 Customer Fuzzy Matching không cần AI

Vấn đề: `CustomerResolver` hiện dùng simple string matching. Cải tiến bằng **fuzzy matching** — không cần AI mà vẫn bắt được "Dreamtech VN", "DRT", "DREAMTECH VIETNAM":

```python
# pip install rapidfuzz (nhẹ hơn fuzzywuzzy)
from rapidfuzz import fuzz, process

class CustomerResolver:
    def resolve(self, value: str) -> NormalizedValue:
        # Exact match → trả về ngay
        if value.lower() in self._cache:
            return NormalizedValue(...)
        
        # Fuzzy match với rapidfuzz (không cần AI!)
        candidates = list(self._cache.keys())
        match, score, _ = process.extractOne(
            value.lower(), candidates, scorer=fuzz.token_set_ratio
        )
        
        if score >= 80:
            return NormalizedValue(..., confidence=score/100)
        
        # Chỉ gọi AI nếu fuzzy score < 80
        return await self._ai_resolve(value)
```

### 5.4 Progressive Confidence Escalation

```
Excel Row ──► Rule Match (free)
    │
    ├── confidence ≥ 0.95 → Accept immediately, no AI needed
    │
    ├── confidence 0.7-0.95 → Haiku validation ($0.001)
    │
    ├── confidence 0.5-0.7 → Sonnet review ($0.003)
    │
    └── confidence < 0.5 → Flag for human review (no AI cost)
```

---

## 6. ƯỚC TÍNH TÁC ĐỘNG

| Tối ưu | Chi phí hiện tại | Sau tối ưu | Tiết kiệm |
|--------|-----------------|------------|-----------|
| Model Routing | $X | $0.3X | ~70% |
| Prompt Caching | $X | $0.15X | ~85% |
| Schema Cache | $X | $0.05X | ~95% |
| Structured Output | N/A | Giảm 90% lỗi | Stability |
| Fuzzy Customer Match | AI calls | 0 AI calls | ~100% cho task này |

**Tổng hợp: Giảm 80-90% chi phí AI với cùng chất lượng output, đồng thời tăng reliability lên đáng kể.**

---

## 7. DATABASE ADDITIONS ĐỀ XUẤT

```sql
-- Thêm vào Supabase để hỗ trợ AI optimization

-- 1. Schema cache
CREATE TABLE excel_schema_cache (
    headers_hash    TEXT PRIMARY KEY,
    headers_preview TEXT,
    schema_json     JSONB NOT NULL,
    hit_count       INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ DEFAULT NOW() + INTERVAL '30 days'
);

-- 2. AI cost tracking
CREATE TABLE ai_usage_log (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_type       TEXT NOT NULL,
    model_used      TEXT NOT NULL,
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    cached_tokens   INTEGER DEFAULT 0,
    cost_usd        DECIMAL(10,6),
    confidence_out  FLOAT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Human correction feedback (để cải thiện AI theo thời gian)
CREATE TABLE ai_corrections (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    task_type       TEXT NOT NULL,
    original_input  JSONB,
    ai_output       JSONB,
    corrected_by    UUID REFERENCES users(id),
    correction      JSONB NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

*Báo cáo này dựa trên: cấu trúc repo GitHub `Socgaumeo/5P-SLMS`, tài liệu GIAI_PHAP_2_FLEXIBLE_EXCEL_PARSER.md, và context dự án 5P Vietnam SLMS*
