# 📚 HƯỚNG DẪN TÍCH HỢP AI PIPELINE
## SLMS - 5P Vietnam

---

## 📁 CẤU TRÚC FILES

```
backend/app/ai/                     # ← COPY TOÀN BỘ THƯ MỤC NÀY
├── __init__.py                     # Module exports
├── pipeline.py                     # Main orchestrator
├── preprocessor.py                 # Stage 1: Text/Image/Excel
├── intent_classifier.py            # Stage 2: Intent classification
├── context_loader.py               # Stage 3: Load from DB
├── entity_extractor.py             # Stage 4: Extract entities
├── validator.py                    # Stage 5: Validate
└── prompts/
    ├── __init__.py
    ├── intent_prompts.py           # Intent classification prompt
    ├── booking_prompts.py          # Booking extraction prompt
    ├── vehicle_prompts.py          # Vehicle extraction prompt
    └── status_prompts.py           # Status extraction prompt
```

---

## 🔧 BƯỚC 1: CÀI ĐẶT DEPENDENCIES

Thêm vào `requirements.txt`:

```txt
# AI Pipeline dependencies
pydantic>=2.0
pandas>=2.0          # For Excel parsing
pypdf>=4.0           # For PDF extraction (optional)
```

Cài đặt:

```bash
pip install pydantic pandas pypdf
```

---

## 🔧 BƯỚC 2: CẤU HÌNH AI CLIENT

### Option A: Nếu đã có AI client

Đảm bảo AI client có các methods:

```python
class AIClient:
    async def generate(
        self, 
        prompt: str, 
        response_format: str = "text",  # "text" hoặc "json"
        temperature: float = 0.7
    ) -> dict | str:
        """Generate text response"""
        pass
    
    async def generate_with_image(
        self,
        prompt: str,
        image_base64: str,
        temperature: float = 0.7
    ) -> dict:
        """Generate response with image (for OCR)"""
        pass
```

### Option B: Tạo Gemini client wrapper

Tạo file `backend/app/core/ai_client.py`:

```python
import google.generativeai as genai
import json
import re

class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
    
    async def generate(
        self, 
        prompt: str, 
        response_format: str = "text",
        temperature: float = 0.7
    ) -> dict | str:
        
        config = genai.GenerationConfig(temperature=temperature)
        
        if response_format == "json":
            config.response_mime_type = "application/json"
        
        response = await self.model.generate_content_async(
            prompt,
            generation_config=config
        )
        
        text = response.text
        
        if response_format == "json":
            # Parse JSON from response
            try:
                return json.loads(text)
            except:
                # Try to extract JSON from markdown
                match = re.search(r"```(?:json)?\\s*(\\{.*?\\})\\s*```", text, re.DOTALL)
                if match:
                    return json.loads(match.group(1))
                raise ValueError("Failed to parse JSON response")
        
        return text
    
    async def generate_with_image(
        self,
        prompt: str,
        image_base64: str,
        temperature: float = 0.7
    ) -> dict:
        
        import base64
        
        # Create image part
        image_data = base64.b64decode(image_base64)
        
        response = await self.model.generate_content_async(
            [prompt, {"mime_type": "image/png", "data": image_data}],
            generation_config=genai.GenerationConfig(temperature=temperature)
        )
        
        return {"text": response.text}
```

---

## 🔧 BƯỚC 3: CẤU HÌNH DATABASE SESSION

### Nếu dùng SQLAlchemy async:

```python
# backend/app/core/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/slms"

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### Nếu dùng databases library:

```python
# backend/app/core/database.py

from databases import Database

DATABASE_URL = "postgresql://user:pass@localhost/slms"
database = Database(DATABASE_URL)

# Wrapper để tương thích với pipeline
class DBSession:
    def __init__(self, db: Database):
        self.db = db
    
    async def fetch_all(self, query: str):
        return await self.db.fetch_all(query)
    
    async def fetch_one(self, query: str):
        return await self.db.fetch_one(query)
```

---

## 🔧 BƯỚC 4: CẬP NHẬT CHAT API ENDPOINT

Cập nhật file `backend/app/api/chat.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import base64

from app.core.database import get_db
from app.core.ai_client import GeminiClient
from app.core.config import settings
from app.ai import AIPipeline, PipelineInput, InputType
from app.ai.preprocessor import detect_input_type

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize AI client
ai_client = GeminiClient(api_key=settings.GEMINI_API_KEY)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    intent: str
    confidence: float
    entities: dict
    is_valid: bool
    missing_fields: list
    suggested_action: str
    clarification_question: Optional[str]
    suggestions: Optional[list]
    processing_time_ms: int


@router.post("/process", response_model=ChatResponse)
async def process_message(
    request: ChatRequest,
    db = Depends(get_db)
):
    """
    Process text message through AI pipeline
    """
    
    pipeline = AIPipeline(db, ai_client)
    
    result = await pipeline.process(PipelineInput(
        content=request.message,
        input_type=InputType.TEXT,
        user_context=request.context,
        session_id=request.session_id
    ))
    
    return ChatResponse(
        intent=result.intent,
        confidence=result.confidence,
        entities=result.entities,
        is_valid=result.is_valid,
        missing_fields=result.missing_fields,
        suggested_action=result.suggested_action,
        clarification_question=result.clarification_question,
        suggestions=result.input_suggestions,
        processing_time_ms=result.processing_time_ms
    )


@router.post("/process-file", response_model=ChatResponse)
async def process_file(
    file: UploadFile = File(...),
    message: str = "",
    session_id: Optional[str] = None,
    db = Depends(get_db)
):
    """
    Process file (image/excel/pdf) through AI pipeline
    """
    
    # Read file
    file_data = await file.read()
    
    # Detect input type
    input_type = detect_input_type(file.filename, file.content_type)
    
    pipeline = AIPipeline(db, ai_client)
    
    result = await pipeline.process(PipelineInput(
        content=message,
        input_type=InputType(input_type),
        file_data=file_data,
        file_name=file.filename,
        session_id=session_id
    ))
    
    return ChatResponse(
        intent=result.intent,
        confidence=result.confidence,
        entities=result.entities,
        is_valid=result.is_valid,
        missing_fields=result.missing_fields,
        suggested_action=result.suggested_action,
        clarification_question=result.clarification_question,
        suggestions=result.input_suggestions,
        processing_time_ms=result.processing_time_ms
    )


# ══════════════════════════════════════════════════════════════════════════════
# ACTION ENDPOINTS (sau khi user confirm)
# ══════════════════════════════════════════════════════════════════════════════

class CreateJobRequest(BaseModel):
    entities: dict
    confirmed: bool = True


@router.post("/actions/create-job")
async def create_job(
    request: CreateJobRequest,
    db = Depends(get_db)
):
    """
    Create job after user confirmation
    """
    if not request.confirmed:
        raise HTTPException(400, "Job not confirmed")
    
    entities = request.entities
    
    # Insert into database
    # (Implement theo logic hiện tại của bạn)
    
    # Generate vendor message
    from app.services.message_generator import generate_vendor_request
    vendor_message = generate_vendor_request(entities)
    
    return {
        "success": True,
        "job_id": "...",
        "job_no": "...",
        "vendor_message": vendor_message
    }


@router.post("/actions/assign-vehicle")
async def assign_vehicle(
    request: CreateJobRequest,
    db = Depends(get_db)
):
    """
    Assign vehicle to job after user confirmation
    """
    entities = request.entities
    
    # Update job with vehicle info
    # (Implement theo logic hiện tại của bạn)
    
    # Generate customer confirmation message
    from app.services.message_generator import generate_customer_confirm
    customer_message = generate_customer_confirm(entities)
    
    return {
        "success": True,
        "job_no": entities.get("matched_job_no"),
        "customer_message": customer_message
    }
```

---

## 🔧 BƯỚC 5: THÊM ROUTES VÀO MAIN APP

Cập nhật `backend/app/main.py`:

```python
from fastapi import FastAPI
from app.api import chat  # Import chat router

app = FastAPI(title="SLMS API")

# Include routers
app.include_router(chat.router)
# ... other routers
```

---

## 🔧 BƯỚC 6: CẬP NHẬT CONFIG

Cập nhật `backend/app/core/config.py`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    
    # AI
    GEMINI_API_KEY: str
    DEEPSEEK_API_KEY: str = ""  # Optional backup
    
    # AI Pipeline settings
    AI_MODEL: str = "gemini-2.0-flash-exp"
    AI_TEMPERATURE_INTENT: float = 0.1
    AI_TEMPERATURE_EXTRACT: float = 0.2
    
    # Confidence thresholds
    CONFIDENCE_HIGH: float = 0.85
    CONFIDENCE_MEDIUM: float = 0.65
    CONFIDENCE_LOW: float = 0.40
    
    class Config:
        env_file = ".env"

settings = Settings()
```

Cập nhật `.env`:

```env
DATABASE_URL=postgresql://user:pass@localhost/slms
GEMINI_API_KEY=your_gemini_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
```

---

## 🧪 BƯỚC 7: TEST

### Test với curl:

```bash
# Test text message
curl -X POST http://localhost:8000/api/chat/process \
  -H "Content-Type: application/json" \
  -d '{"message": "Ngày mai 22h cần xe 1.25T cho DRT1"}'

# Test file upload
curl -X POST http://localhost:8000/api/chat/process-file \
  -F "file=@booking.xlsx" \
  -F "message=Parse file này"
```

### Test với Python:

```python
import asyncio
from app.core.database import get_db
from app.core.ai_client import GeminiClient
from app.ai import AIPipeline, PipelineInput, InputType

async def test_pipeline():
    # Setup
    db = ...  # Your database session
    ai = GeminiClient(api_key="your_key")
    
    pipeline = AIPipeline(db, ai)
    
    # Test cases
    test_cases = [
        "Ngày mai 22h cần xe 1.25T cho DRT1",
        "BKS 29H 76514 - Nguyễn Văn A - 0912345678",
        "Job TRK-2601-089 đã giao xong",
        "anh ơi mai lấy hàng nhé",
    ]
    
    for text in test_cases:
        result = await pipeline.process(PipelineInput(
            content=text,
            input_type=InputType.TEXT
        ))
        
        print(f"Input: {text}")
        print(f"Intent: {result.intent} ({result.confidence:.2f})")
        print(f"Entities: {result.entities}")
        print(f"Action: {result.suggested_action}")
        print("-" * 50)

asyncio.run(test_pipeline())
```

---

## ✅ CHECKLIST SAU KHI TÍCH HỢP

- [ ] Copy folder `backend/app/ai/` vào project
- [ ] Cài dependencies: `pip install pydantic pandas`
- [ ] Tạo/cập nhật AI client wrapper
- [ ] Cập nhật `chat.py` với new endpoints
- [ ] Cập nhật `config.py` với AI settings
- [ ] Thêm API keys vào `.env`
- [ ] Test với các test cases
- [ ] Update frontend để gọi new API

---

## 🚀 FRONTEND INTEGRATION

Frontend cần gọi API và xử lý response:

```javascript
// services/chatApi.js

export async function processMessage(message, sessionId) {
  const response = await fetch('/api/chat/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId })
  });
  return response.json();
}

export async function processFile(file, message, sessionId) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('message', message || '');
  if (sessionId) formData.append('session_id', sessionId);
  
  const response = await fetch('/api/chat/process-file', {
    method: 'POST',
    body: formData
  });
  return response.json();
}
```

```javascript
// components/ChatUI.jsx

function handleAIResponse(result) {
  switch (result.suggested_action) {
    case 'show_form':
      // Show pre-filled form with result.entities
      showConfirmationForm(result.entities);
      break;
    
    case 'ask_clarification':
      // Show clarification question
      showMessage('AI', result.clarification_question);
      if (result.suggestions) {
        showSuggestions(result.suggestions);
      }
      break;
    
    case 'cannot_understand':
      // Show error with suggestions
      showMessage('AI', result.clarification_question);
      showSuggestions(result.suggestions);
      break;
  }
}
```

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề khi tích hợp, kiểm tra:

1. **AI Client**: Đảm bảo có API key và client hoạt động
2. **Database**: Đảm bảo có dữ liệu customers, routes trong DB
3. **Logs**: Bật logging để debug pipeline stages
4. **Test từng stage**: Test IntentClassifier riêng trước khi test full pipeline
