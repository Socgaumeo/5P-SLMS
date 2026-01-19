# 🤖 MODULE 4.1: AI ARCHITECTURE

## 📋 Mục lục
1. [AI Overview](#1-ai-overview)
2. [AI Service Design](#2-ai-service-design)
3. [Model Selection](#3-model-selection)
4. [Cost Optimization](#4-cost-optimization)

---

## 1. AI Overview

### 1.1 AI Role in SLMS

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          AI IN SLMS                                              │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                     CORE AI FUNCTIONS                                   │   │
│   │                                                                          │   │
│   │  1. 📥 INPUT PROCESSING                                                 │   │
│   │     • Parse Excel booking files                                         │   │
│   │     • Extract data from Zalo messages                                   │   │
│   │     • OCR images (invoices, PODs)                                      │   │
│   │     • Understand natural language requests                              │   │
│   │                                                                          │   │
│   │  2. 🧠 INTELLIGENT ROUTING                                              │   │
│   │     • Detect user intent                                                │   │
│   │     • Route to appropriate action                                       │   │
│   │     • Handle ambiguous requests                                         │   │
│   │                                                                          │   │
│   │  3. 📤 OUTPUT GENERATION                                                │   │
│   │     • Generate customer confirmation messages                           │   │
│   │     • Create vendor dispatch requests                                   │   │
│   │     • Format reports and summaries                                      │   │
│   │                                                                          │   │
│   │  4. 🔄 WORKFLOW AUTOMATION                                              │   │
│   │     • Auto-create jobs from messages                                    │   │
│   │     • Auto-update jobs from vendor responses                            │   │
│   │     • Auto-notify relevant parties                                      │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 AI Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       AI PROCESSING PIPELINE                                     │
│                                                                                  │
│   INPUT                    PROCESSING                      OUTPUT               │
│   ──────                   ──────────                      ──────               │
│                                                                                  │
│   ┌─────────┐         ┌───────────────────┐         ┌─────────────┐            │
│   │  Zalo   │────────►│                   │────────►│ Create Job  │            │
│   │ Message │         │                   │         └─────────────┘            │
│   └─────────┘         │                   │                                     │
│                       │   ┌───────────┐   │         ┌─────────────┐            │
│   ┌─────────┐         │   │   INTENT  │   │────────►│ Update Job  │            │
│   │  Excel  │────────►│   │ DETECTION │   │         └─────────────┘            │
│   │  File   │         │   └───────────┘   │                                     │
│   └─────────┘         │         │         │         ┌─────────────┐            │
│                       │         ▼         │────────►│  Query DB   │            │
│   ┌─────────┐         │   ┌───────────┐   │         └─────────────┘            │
│   │  Image  │────────►│   │  ENTITY   │   │                                     │
│   │  (OCR)  │         │   │EXTRACTION │   │         ┌─────────────┐            │
│   └─────────┘         │   └───────────┘   │────────►│  Generate   │            │
│                       │         │         │         │   Message   │            │
│   ┌─────────┐         │         ▼         │         └─────────────┘            │
│   │  Voice  │────────►│   ┌───────────┐   │                                     │
│   │ (STT)   │         │   │  ACTION   │   │         ┌─────────────┐            │
│   └─────────┘         │   │ EXECUTOR  │   │────────►│  Send Alert │            │
│                       │   └───────────┘   │         └─────────────┘            │
│                       │                   │                                     │
│                       └───────────────────┘                                     │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. AI Service Design

### 2.1 Service Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       AI SERVICE ARCHITECTURE                                    │
│                                                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                         API GATEWAY                                     │   │
│   │                                                                          │   │
│   │  POST /api/ai/process                                                   │   │
│   │  POST /api/ai/parse-file                                                │   │
│   │  POST /api/ai/generate-message                                          │   │
│   │                                                                          │   │
│   └────────────────────────────────┬────────────────────────────────────────┘   │
│                                    │                                            │
│                                    ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                       AI SERVICE LAYER                                  │   │
│   │                                                                          │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │   │
│   │  │   Intent     │  │   Entity     │  │   Document   │  │  Message   │  │   │
│   │  │  Detector    │  │  Extractor   │  │   Parser     │  │ Generator  │  │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │   │
│   │                                                                          │   │
│   └────────────────────────────────┬────────────────────────────────────────┘   │
│                                    │                                            │
│                                    ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────────┐   │
│   │                       MODEL PROVIDERS                                   │   │
│   │                                                                          │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │   │
│   │  │   Gemini     │  │   Claude     │  │  Document    │  │   Local    │  │   │
│   │  │   Flash      │  │   (Backup)   │  │     AI       │  │   Models   │  │   │
│   │  │   $0.075/1M  │  │   $3/1M      │  │   (OCR)      │  │  (Future)  │  │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │   │
│   │                                                                          │   │
│   └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 AI Service Interface

```python
# ai_service.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class Intent(Enum):
    CREATE_JOB = "create_job"
    UPDATE_JOB = "update_job"
    ASSIGN_VEHICLE = "assign_vehicle"
    COMPLETE_JOB = "complete_job"
    QUERY_STATUS = "query_status"
    GENERATE_STATEMENT = "generate_statement"
    CREATE_RATE = "create_rate"
    UNKNOWN = "unknown"
    HELP = "help"

@dataclass
class AIRequest:
    source: str                     # ZALO, EMAIL, MANUAL
    source_id: str                  # Room name, email address
    content_type: str               # TEXT, FILE, IMAGE
    content: str                    # Message text or file path
    context: Optional[Dict] = None  # Previous messages, job reference
    
@dataclass
class AIResponse:
    intent: Intent
    confidence: float
    entities: Dict[str, Any]
    action: Optional[str]
    message: Optional[str]
    error: Optional[str]

class AIService(ABC):
    @abstractmethod
    async def process(self, request: AIRequest) -> AIResponse:
        """Process an AI request and return response"""
        pass
    
    @abstractmethod
    async def detect_intent(self, text: str, context: Dict = None) -> tuple[Intent, float]:
        """Detect intent from text"""
        pass
    
    @abstractmethod
    async def extract_entities(self, text: str, intent: Intent) -> Dict[str, Any]:
        """Extract entities based on intent"""
        pass
    
    @abstractmethod
    async def parse_document(self, file_path: str, doc_type: str) -> Dict[str, Any]:
        """Parse document and extract structured data"""
        pass
    
    @abstractmethod
    async def generate_message(self, template: str, data: Dict) -> str:
        """Generate message from template"""
        pass


class GeminiAIService(AIService):
    """Gemini-based AI Service implementation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "gemini-2.0-flash"
        
    async def process(self, request: AIRequest) -> AIResponse:
        # Detect intent
        intent, confidence = await self.detect_intent(
            request.content, 
            request.context
        )
        
        # Extract entities based on intent
        entities = await self.extract_entities(request.content, intent)
        
        # Determine action
        action = self._get_action(intent, entities)
        
        # Generate response message
        message = await self._generate_response(intent, entities)
        
        return AIResponse(
            intent=intent,
            confidence=confidence,
            entities=entities,
            action=action,
            message=message,
            error=None
        )
    
    async def detect_intent(self, text: str, context: Dict = None) -> tuple[Intent, float]:
        prompt = f"""Phân loại intent của tin nhắn sau.

Tin nhắn: {text}

Context: {context or 'None'}

Các intent có thể:
- create_job: Tạo booking/job mới
- update_job: Cập nhật job đã có
- assign_vehicle: Gán xe/lái xe cho job
- complete_job: Hoàn thành job
- query_status: Hỏi trạng thái
- generate_statement: Tạo bảng kê
- create_rate: Tạo/cập nhật báo giá
- help: Hỏi hướng dẫn
- unknown: Không xác định

Trả lời format: intent_name|confidence_score (0.0-1.0)
"""
        response = await self._call_gemini(prompt)
        parts = response.strip().split('|')
        intent_str = parts[0]
        confidence = float(parts[1]) if len(parts) > 1 else 0.8
        
        return Intent(intent_str), confidence
    
    async def extract_entities(self, text: str, intent: Intent) -> Dict[str, Any]:
        entity_prompts = {
            Intent.CREATE_JOB: """Trích xuất thông tin booking:
- customer_code: Mã khách hàng (VD: DRT1, SEVT)
- booking_date: Ngày lấy hàng (format: YYYY-MM-DD)
- pickup_time: Giờ lấy hàng (format: HH:MM)
- invoice_numbers: Số invoice (có thể nhiều, phân cách bởi dấu phẩy)
- cargo_type: Loại hàng (VD: PCB, TEXTILE)
- package_info: Thông tin đóng gói (VD: 8 box, 5 pallets)
- vehicle_type: Loại xe yêu cầu (VD: 1.25T, 2.5T)
- pickup_address: Địa chỉ lấy hàng
- delivery_address: Địa chỉ giao hàng
- notes: Ghi chú thêm""",

            Intent.ASSIGN_VEHICLE: """Trích xuất thông tin xe/lái xe:
- job_reference: Mã job hoặc thông tin tham chiếu
- license_plate: Biển số xe (VD: 29H 76514)
- driver_name: Tên lái xe
- driver_phone: Số điện thoại lái xe
- driver_id_card: Số CCCD/CMND
- vehicle_type: Loại xe""",

            Intent.QUERY_STATUS: """Trích xuất thông tin truy vấn:
- job_number: Mã job (VD: TRK-2601-0001)
- customer_code: Mã khách hàng
- date_range: Khoảng thời gian
- status_filter: Lọc theo trạng thái""",
        }
        
        prompt = entity_prompts.get(intent, "Trích xuất các thông tin chính từ tin nhắn.")
        
        full_prompt = f"""{prompt}

Tin nhắn: {text}

Trả lời dạng JSON, chỉ bao gồm các trường có giá trị."""
        
        response = await self._call_gemini(full_prompt)
        
        # Parse JSON response
        import json
        try:
            entities = json.loads(response)
        except:
            entities = {}
            
        return entities
    
    async def parse_document(self, file_path: str, doc_type: str) -> Dict[str, Any]:
        """Parse Excel, PDF, or Image documents"""
        
        if doc_type == 'EXCEL':
            return await self._parse_excel(file_path)
        elif doc_type == 'IMAGE':
            return await self._parse_image(file_path)
        elif doc_type == 'PDF':
            return await self._parse_pdf(file_path)
        else:
            raise ValueError(f"Unsupported document type: {doc_type}")
    
    async def _parse_excel(self, file_path: str) -> Dict[str, Any]:
        """Parse Excel booking file"""
        import pandas as pd
        
        df = pd.read_excel(file_path)
        
        # Extract booking info using AI
        content = df.to_string()
        
        prompt = f"""Đây là nội dung file Excel phiếu book xe.
Hãy trích xuất thông tin booking.

{content}

Trả lời dạng JSON với các trường:
- customer_name
- contact_name
- contact_phone
- booking_date
- pickup_time
- invoices (list)
- cargo_type
- package_info
- pickup_address
- delivery_address
"""
        
        response = await self._call_gemini(prompt)
        
        import json
        return json.loads(response)
    
    async def generate_message(self, template: str, data: Dict) -> str:
        """Generate message using template and data"""
        
        prompt = f"""Tạo tin nhắn dựa trên template và dữ liệu.

Template: {template}

Data: {data}

Yêu cầu:
- Giữ nguyên format template
- Thay thế các placeholder bằng dữ liệu
- Đảm bảo tin nhắn ngắn gọn, chuyên nghiệp
"""
        
        return await self._call_gemini(prompt)
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        import google.generativeai as genai
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)
        
        response = model.generate_content(prompt)
        return response.text
```

---

## 3. Model Selection

### 3.1 Model Comparison

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          MODEL COMPARISON                                        │
│                                                                                  │
│   Model              │ Strength       │ Cost/1M tokens │ Use Case               │
│   ───────────────────┼────────────────┼────────────────┼─────────────────────── │
│   Gemini 2.0 Flash   │ Fast, Cheap    │ $0.075 input   │ Primary: Intent,       │
│                      │ Good accuracy  │ $0.30 output   │ Entity extraction      │
│   ───────────────────┼────────────────┼────────────────┼─────────────────────── │
│   Gemini 1.5 Pro     │ Best quality   │ $1.25 input    │ Complex reasoning,     │
│                      │ Long context   │ $5.00 output   │ Document analysis      │
│   ───────────────────┼────────────────┼────────────────┼─────────────────────── │
│   Claude 3.5 Sonnet  │ Best reasoning │ $3.00 input    │ Fallback, Complex      │
│                      │ Vietnamese OK  │ $15.00 output  │ cases                  │
│   ───────────────────┼────────────────┼────────────────┼─────────────────────── │
│   Document AI        │ Best OCR       │ $1.50/1000     │ Image/PDF extraction   │
│   (Google Cloud)     │ Structured     │ pages          │                        │
│   ───────────────────┼────────────────┼────────────────┼─────────────────────── │
│   Local LLM          │ Free, Private  │ $0 (hardware)  │ Future: Simple tasks   │
│   (Llama, Qwen)      │ No internet    │                │                        │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Model Selection Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      MODEL SELECTION STRATEGY                                    │
│                                                                                  │
│   Task Type                    │ Primary Model        │ Fallback               │
│   ─────────────────────────────┼──────────────────────┼─────────────────────── │
│   Intent Detection             │ Gemini 2.0 Flash     │ Claude 3.5 Sonnet     │
│   Entity Extraction (Text)     │ Gemini 2.0 Flash     │ Gemini 1.5 Pro        │
│   Document Parsing (Excel)     │ Gemini 2.0 Flash     │ -                      │
│   Document Parsing (Image/PDF) │ Document AI          │ Gemini 1.5 Pro        │
│   Message Generation           │ Gemini 2.0 Flash     │ -                      │
│   Complex Reasoning            │ Gemini 1.5 Pro       │ Claude 3.5 Sonnet     │
│                                                                                  │
│   Selection Logic:                                                              │
│   ──────────────                                                                │
│   1. Try primary model                                                          │
│   2. If confidence < 0.7, try fallback                                         │
│   3. If fallback fails, return UNKNOWN with low confidence                     │
│   4. Log all attempts for analysis                                             │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Cost Optimization

### 4.1 Cost Estimation

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         COST ESTIMATION                                          │
│                                                                                  │
│   Daily Volume (Estimated):                                                     │
│   ────────────────────────                                                      │
│   • Customer bookings: 20-30 messages/day                                       │
│   • Vendor responses: 20-30 messages/day                                        │
│   • Status queries: 10-20 messages/day                                          │
│   • Document parsing: 5-10 files/day                                            │
│   • Message generation: 30-50 messages/day                                      │
│   ────────────────────────────────────────                                      │
│   Total: ~100-150 AI requests/day                                               │
│                                                                                  │
│   Token Usage per Request:                                                      │
│   ────────────────────────                                                      │
│   • Intent detection: ~200 input + ~50 output = 250 tokens                     │
│   • Entity extraction: ~500 input + ~200 output = 700 tokens                   │
│   • Document parsing: ~2000 input + ~500 output = 2500 tokens                  │
│   • Message generation: ~300 input + ~150 output = 450 tokens                  │
│   ────────────────────────────────────────                                      │
│   Average: ~1000 tokens/request                                                 │
│                                                                                  │
│   Monthly Cost (Gemini Flash):                                                  │
│   ───────────────────────────                                                   │
│   • 150 requests × 30 days = 4,500 requests/month                              │
│   • 4,500 × 1000 tokens = 4.5M tokens/month                                    │
│   • Input cost: 3M × $0.075/1M = $0.225                                        │
│   • Output cost: 1.5M × $0.30/1M = $0.45                                       │
│   ────────────────────────────────────────                                      │
│   Total: ~$0.70/month (chưa đến $1!)                                           │
│                                                                                  │
│   + Document AI (OCR): ~$5-10/month                                            │
│   + Buffer (complex cases): ~$5/month                                          │
│   ════════════════════════════════════                                          │
│   TOTAL AI COST: ~$10-15/month                                                 │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Cost Optimization Strategies

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     COST OPTIMIZATION STRATEGIES                                 │
│                                                                                  │
│   1. CACHING                                                                    │
│      ──────────                                                                 │
│      • Cache intent detection for similar messages                              │
│      • Cache entity extraction patterns                                         │
│      • Cache message templates                                                  │
│      Expected savings: 30-50%                                                   │
│                                                                                  │
│   2. BATCHING                                                                   │
│      ──────────                                                                 │
│      • Batch similar requests together                                          │
│      • Process multiple entities in one call                                    │
│      • Reduce API overhead                                                      │
│      Expected savings: 20-30%                                                   │
│                                                                                  │
│   3. PROMPT OPTIMIZATION                                                        │
│      ───────────────────                                                        │
│      • Shorter, more focused prompts                                            │
│      • Structured output format                                                 │
│      • Few-shot examples instead of long instructions                          │
│      Expected savings: 20-40%                                                   │
│                                                                                  │
│   4. MODEL TIERING                                                              │
│      ──────────────                                                             │
│      • Use cheapest model first                                                 │
│      • Escalate only when needed                                                │
│      • Track success rates per model                                            │
│      Expected savings: 50-70%                                                   │
│                                                                                  │
│   5. LOCAL PROCESSING                                                           │
│      ─────────────────                                                          │
│      • Rule-based intent for common patterns                                    │
│      • Regex for entity extraction                                              │
│      • Template-based message generation                                        │
│      Expected savings: 40-60%                                                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 AI Logging Table

```sql
CREATE TABLE ai_logs (
    id              BIGSERIAL PRIMARY KEY,
    
    -- Request
    request_id      UUID DEFAULT gen_random_uuid(),
    request_type    VARCHAR(50) NOT NULL,           -- INTENT, ENTITY, DOCUMENT, MESSAGE
    source          VARCHAR(50),                    -- ZALO, EMAIL, MANUAL
    input_text      TEXT,
    input_tokens    INTEGER,
    
    -- Model
    model_used      VARCHAR(50) NOT NULL,           -- gemini-2.0-flash, claude-3.5-sonnet
    model_provider  VARCHAR(20),                    -- GOOGLE, ANTHROPIC
    
    -- Response
    output_text     TEXT,
    output_tokens   INTEGER,
    confidence      DECIMAL(3,2),
    
    -- Action taken
    intent_detected VARCHAR(50),
    entities_extracted JSONB,
    action_result   VARCHAR(20),                    -- SUCCESS, FAILED, PARTIAL
    action_entity_id INTEGER,                       -- Created/updated record ID
    error_message   TEXT,
    
    -- Performance
    processing_time_ms INTEGER,
    cost_usd        DECIMAL(10,6),
    
    -- Timestamps
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_ai_logs_type ON ai_logs(request_type);
CREATE INDEX idx_ai_logs_model ON ai_logs(model_used);
CREATE INDEX idx_ai_logs_date ON ai_logs(created_at);
CREATE INDEX idx_ai_logs_intent ON ai_logs(intent_detected);
```

---

## 📊 SUMMARY

### Architecture Components
1. **AI Service** - Central module for all AI operations
2. **Intent Detection** - Classify user requests
3. **Entity Extraction** - Extract structured data
4. **Document Parsing** - Handle files/images
5. **Message Generation** - Create outputs

### Model Selection
- **Primary**: Gemini 2.0 Flash (fast, cheap)
- **Fallback**: Gemini 1.5 Pro, Claude 3.5 Sonnet
- **OCR**: Google Document AI

### Cost Estimate
- ~150 requests/day × 30 days = 4,500 requests/month
- Average 1,000 tokens/request
- Gemini Flash: ~$10-15/month total

### Integration Points
- **n8n**: Workflow automation triggers AI
- **Zalo Bot**: Messages routed through AI
- **Database**: All operations logged
