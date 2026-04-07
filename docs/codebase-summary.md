# Codebase Summary

## Project Structure

```
backend/
├── main.py                          # FastAPI app, routes, auth, middleware
├── requirements.txt                 # Python dependencies
├── app/
│   ├── ai/
│   │   ├── anthropic_client.py     # Claude API integration
│   │   ├── deepseek_client.py      # DeepSeek API integration
│   │   ├── gemini_client.py        # Google Gemini integration
│   │   ├── memory/
│   │   │   ├── conversation_manager.py  # Chat memory management
│   │   │   └── continuation_detector.py # Detects conversation continuations
│   │   ├── prompts/
│   │   │   └── unified_logistics_prompt.py # Rate sheet parsing prompt
│   │   └── rate_parser.py          # Standard parser (regex/table extraction)
│   ├── api/
│   │   ├── admin.py                # Admin router, user management (auth required)
│   │   ├── jobs.py                 # Job management endpoints
│   │   ├── quotations.py           # Quotation endpoints
│   │   └── files.py                # File upload/download
│   ├── core/
│   │   ├── config.py               # Environment configuration
│   │   └── security.py             # JWT verification, password hashing
│   ├── models.py                   # SQLAlchemy models (RateRow, Quotation, Job, User)
│   └── database.py                 # Database session management
├── tests/
│   └── test_*.py                   # Unit and integration tests
└── scripts/
    └── migrate-supabase-*.py       # Database migration scripts
```

## Key Components

### Authentication & Security
**Location**: `backend/main.py`, `backend/app/core/security.py`

- JWT token generation and validation
- Password hashing (bcrypt)
- Dependency: `verify_jwt` for protected endpoints
- Rate limiting: 100/min default, 5/min login

**Middleware**:
- `SecurityHeadersMiddleware` — HSTS, X-Frame-Options, CSP headers
- `GZipMiddleware` — Response compression

### Rate Sheet Parser
**Location**: `backend/app/ai/rate_parser.py`, `backend/app/ai/prompts/unified_logistics_prompt.py`

**Standard Parser**:
- Extracts routes, rates from structured rate sheets
- Returns confidence score
- Fast, regex-based

**AI Fallback** (triggered when confidence < 60%):
- Uses Claude API via `anthropic_client.py`
- Extracts: origin, destination, rates, surcharges, notes
- Handles unstructured/complex formats

**RateRow Model** (`backend/app/models.py`):
```python
class RateRow(Base):
    origin: str
    destination: str
    service_type_code: str
    base_rate: float
    surcharge: Optional[float]  # NEW
    is_surcharge: bool          # NEW
    confidence_score: float
    source: str  # 'standard' or 'ai'
```

### API Endpoints (all require JWT)

**Quotation Management** (`backend/app/api/quotations.py`)
- `GET /api/quotations` — List with filters
- `POST /api/quotations` — Create
- `GET /api/quotations/{id}` — Detail
- `PUT /api/quotations/{id}` — Update
- `DELETE /api/quotations/{id}` — Delete

**Job Management** (`backend/app/api/jobs.py`)
- `GET /api/jobs` — List jobs
- `POST /api/jobs` — Create job
- `PATCH /api/jobs/{id}` — Update status

**Admin Routes** (`backend/app/api/admin.py`, requires manager/admin role)
- User CRUD operations
- Protected by `require_manager_or_admin`

**File Management** (`backend/app/api/files.py`)
- `POST /api/files/upload` — Upload rate sheet
- `GET /api/files/{id}` — Download

### AI Integration
**Location**: `backend/app/ai/`

- **Anthropic Client**: Claude API calls for rate parsing
- **DeepSeek Client**: Alternative LLM provider
- **Gemini Client**: Google Gemini integration
- **Conversation Manager**: Maintains chat history
- **Continuation Detector**: Detects multi-turn conversations

### Configuration
**Location**: `backend/app/core/config.py`

- Database URL (Supabase PostgreSQL)
- API keys for AI providers
- JWT secret, expiration
- CORS settings
- Environment-based config (dev/prod)

## Database Schema

**Primary Tables**:
- `users` — User accounts (email, password_hash, role)
- `quotations` — Shipping quotations
- `jobs` — Logistics jobs
- `rate_files` — Uploaded rate sheets
- `rate_rows` — Parsed rate data (surcharge, is_surcharge fields)
- `conversation_history` — Chat memory

## Frontend Integration

**Performance**:
- Vite bundle splitting (vendor-react separate)
- Vercel Speed Insights enabled
- API responses gzip-compressed

**API Calls**:
- All requests include JWT in Authorization header
- Handles 401 auth errors, redirects to login
- CORS pre-flight requests allowed

## Development Workflow

1. **Setup**: Install deps (`pip install -r requirements.txt`), set `.env`
2. **Development**: `uvicorn main:app --reload`
3. **Testing**: `pytest tests/`
4. **Deployment**: Docker container with gunicorn

## Key Dependencies
- **FastAPI** — Web framework
- **SQLAlchemy** — ORM
- **Pydantic** — Data validation
- **python-jose** — JWT handling
- **slowapi** — Rate limiting
- **anthropic**, **google-genai**, **deepseek** — LLM providers
- **openpyxl**, **pandas** — File parsing

## Recent Enhancements (Mar 2026)
- JWT auth on all endpoints
- Rate limiting configured
- Security headers middleware
- Input sanitization on search
- AI fallback for rate parsing (< 60% confidence)
- Surcharge field in RateRow model
- Password policy: 8-char minimum
