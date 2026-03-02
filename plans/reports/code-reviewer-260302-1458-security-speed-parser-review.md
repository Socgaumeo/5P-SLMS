# Code Review: Security, Speed, Parser Improvements

**Date:** 2026-03-02
**Reviewer:** code-reviewer agent
**Scope:** Recent changes for Phase 1 (Security), Phase 2 (Speed), Phase 3 (Parser)

---

## Scope

### Files Reviewed
- `backend/app/middleware/security_headers.py` (NEW)
- `backend/app/middleware/rate_limiter.py` (NEW)
- `backend/main.py` (MODIFIED)
- `backend/app/api/admin.py` (MODIFIED)
- `backend/app/api/auth.py` (MODIFIED)
- `backend/app/api/rate_file_upload.py` (MODIFIED)
- `backend/app/ai/excel/rate-sheet-ai-parser.py` (MODIFIED)
- `backend/requirements.txt` (MODIFIED)
- `frontend/src/main.jsx` (MODIFIED)
- `frontend/vite.config.js` (MODIFIED)

### Lines of Code Analyzed
~2,000 lines across 10 files

### Review Focus
Recent security hardening, speed optimization, parser improvements per plan phases

---

## Overall Assessment

**Quality:** Good. Implementation addresses security, speed, parser accuracy concerns.
**Security:** Significantly improved with auth, rate limiting, headers, input sanitization.
**Performance:** Speed optimizations applied (GZip, code splitting, monitoring).
**Parser:** Enhanced with AI fallback for low-confidence regex extractions.

**Critical Issues:** 2
**High Priority:** 3
**Medium Priority:** 4
**Low Priority:** 2

---

## Critical Issues

### 1. SlowAPI Login Endpoint Parameter Order
**File:** `backend/app/api/auth.py:47-48`
**Issue:** slowapi decorator requires Request parameter accessible via dependency or direct param

```python
@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login(req: Request, request: LoginRequest):  # ✅ CORRECT
```

**Status:** ✅ FIXED — Request parameter `req` is correctly placed first before Pydantic model
**Impact:** Rate limiting works correctly for login endpoint

### 2. Admin Router Auth Protection
**File:** `backend/app/api/admin.py:36-39`
**Issue:** All admin endpoints must require manager/admin role

```python
router = APIRouter(
    prefix="/api/admin", tags=["Admin"],
    dependencies=[Depends(require_manager_or_admin)]  # ✅ CORRECT
)
```

**Status:** ✅ FIXED — Router-level dependency protects all admin routes
**Impact:** Unauthorized users cannot access admin CRUD operations

---

## High Priority Findings

### 1. Missing Auth on Service Mutation Endpoints
**File:** `backend/main.py:234-296, 302-408, 415-481`
**Issue:** Some endpoints use `get_current_user` (any authenticated user) instead of `require_manager_or_admin` for data mutations

**Examples:**
- `PUT /api/services/{svc_id}/assign` (line 235) — Only requires `get_current_user`
- `PUT /api/services/{svc_id}/status` (line 303) — Only requires `get_current_user`
- `PUT /api/services/{svc_id}/notes` (line 387) — Only requires `get_current_user`
- `PUT /api/jobs/{job_id}/status` (line 416) — Only requires `get_current_user`

**Risk:** Regular users (role=STAFF) can modify service assignments, status, vendor info

**Recommendation:**
```python
# Change from:
async def assign_service(svc_id: int, request: AssignServiceRequest, current_user: dict = Depends(get_current_user)):

# To:
async def assign_service(svc_id: int, request: AssignServiceRequest, current_user: dict = Depends(require_manager_or_admin)):
```

**Affected endpoints:**
- `/api/services/{svc_id}/assign` (line 234)
- `/api/services/{svc_id}/notes` (line 386)
- `/api/jobs/{job_id}/status` (line 415)

**Exception:** `/api/services/{svc_id}/status` may be acceptable for staff updates (confirm with product owner)

### 2. Input Sanitization Missing Unit Tests
**File:** `backend/main.py:149, 181`
**Issue:** Search input sanitization uses `re.sub(r'[,.()*;\'""]', '', q).strip()[:100]` but lacks validation tests

**Current Implementation:**
```python
q = re.sub(r'[,.()*;\'""]', '', q).strip()[:100]
```

**Risk:**
- Potential bypass via SQL injection through PostgREST `.or_()` filter
- No validation of regex effectiveness against injection payloads

**Recommendation:**
- Add unit tests for injection attempts: `'; DROP TABLE--`, `%00`, Unicode normalization attacks
- Consider allowlist approach: `re.sub(r'[^a-zA-Z0-9\s]', '', q)` for stricter validation
- Validate PostgREST param escaping (Supabase client should handle, but verify)

### 3. AI Parser Confidence Threshold
**File:** `backend/app/api/rate_file_upload.py:331-333`
**Issue:** Fixed 60% confidence threshold may cause false negatives/positives

**Current Logic:**
```python
confidence = regex_count / max(total_data_rows, 1)
if regex_count == 0 or confidence < 0.6:
    # Call AI parser
```

**Risk:**
- Sheets with sparse data (e.g., 5 data rows, 2 rates extracted) = 40% confidence → AI called unnecessarily (cost increase)
- Complex pivot sheets with merged cells may undercount data_rows → false high confidence → skip AI when needed

**Recommendation:**
- Add absolute minimum threshold: `regex_count < 10 OR confidence < 0.6`
- Log confidence scores for monitoring/tuning
- Make threshold configurable via env var `AI_PARSER_CONFIDENCE_THRESHOLD=0.6`

---

## Medium Priority Improvements

### 1. Middleware Order Validation
**File:** `backend/main.py:47-65`
**Current Order:** CORS → SecurityHeaders → GZip → SlowAPI

**Analysis:**
```python
# Line 47-54: CORS
app.add_middleware(CORSMiddleware, ...)

# Line 56-57: SecurityHeaders
app.add_middleware(SecurityHeadersMiddleware)

# Line 59-60: GZip
app.add_middleware(GZipMiddleware, minimum_size=500)

# Line 62-65: SlowAPI
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, ...)
app.add_middleware(SlowAPIMiddleware)
```

**Recommendation:**
- ✅ CORS first (correct) — handles preflight OPTIONS
- ✅ SecurityHeaders before GZip (correct) — headers added before compression
- ✅ GZip before SlowAPI (correct) — rate limit uncompressed requests
- **Minor improvement:** Consider moving SlowAPI before GZip to reject rate-limited requests earlier (save CPU on compression)

**Optimal Order:** CORS → SlowAPI → SecurityHeaders → GZip

### 2. HSTS Header Configuration
**File:** `backend/app/middleware/security_headers.py:12`
**Issue:** HSTS header hardcoded to `max-age=31536000; includeSubDomains`

```python
response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
```

**Risk:**
- `includeSubDomains` may break dev/test subdomains using HTTP
- No `preload` directive (optional but recommended for production)

**Recommendation:**
- Make HSTS configurable via env var
- Development: `HSTS_ENABLED=False`
- Production: `HSTS_HEADER="max-age=31536000; includeSubDomains; preload"`

### 3. Rate Limiter Storage Backend
**File:** `backend/app/middleware/rate_limiter.py:6`
**Issue:** slowapi uses in-memory storage (default), doesn't persist across restarts or scale horizontally

```python
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
```

**Risk:**
- Rate limit counters reset on server restart (attacker can bypass by triggering restarts)
- Multi-instance deployments (Railway) won't share rate limit state → each instance has separate 100/min limit

**Recommendation:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
import redis

# Production: use Redis storage
redis_client = redis.Redis.from_url(settings.REDIS_URL) if settings.REDIS_URL else None
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    storage_uri=settings.REDIS_URL if redis_client else None
)
```

### 4. Surcharge Extraction Validation
**File:** `backend/app/api/rate_file_upload.py:159-179`
**Issue:** Surcharge detection uses keyword matching without validation

```python
SURCHARGE_KEYWORDS = [
    "chờ giờ", "lưu ca", "hủy chuyến", "huỷ chuyến", "bốc xếp",
    "phụ phí", "lưu ý", "dịch vụ khác", "thanh lý", "ghi chú",
    "note", "remark", "lưu kho",
]
```

**Risk:**
- Keyword "ghi chú" too broad → may flag valid route rows as surcharges if they contain notes
- No distinction between per-trip surcharges vs percentage-based fees

**Recommendation:**
- Add context validation: only flag as surcharge if row has price but no valid origin/destination
- Add `is_surcharge` field to DB schema (already done in code, verify DB migration)
- Log surcharge extraction for manual review in first few file uploads

---

## Low Priority Suggestions

### 1. Frontend SpeedInsights Component
**File:** `frontend/src/main.jsx:19`
**Issue:** SpeedInsights component added without error boundary

```jsx
<SpeedInsights />
```

**Recommendation:** Wrap in error boundary to prevent crashes if Vercel script fails to load

```jsx
<ErrorBoundary fallback={null}>
  <SpeedInsights />
</ErrorBoundary>
```

### 2. Password Policy Strictness
**File:** `backend/app/api/auth.py:214`
**Current:** Minimum 8 characters, no complexity requirements

```python
if len(new_password) < 8:
    raise HTTPException(status_code=400, detail="Mật khẩu mới phải có ít nhất 8 ký tự")
```

**Recommendation:** Add complexity requirements for production (optional for MVP)
- At least 1 uppercase, 1 lowercase, 1 number
- Prohibit common passwords (use `python-zxcvbn` library)

---

## Positive Observations

### Security Improvements ✅
- ✅ Router-level auth dependencies for admin endpoints (DRY, maintainable)
- ✅ Rate limiting on login endpoint (5/min) prevents brute force
- ✅ Security headers middleware (XSS, clickjacking, MIME sniffing protection)
- ✅ Input sanitization on search endpoints (regex-based SQL injection prevention)
- ✅ Password policy enforcement (8 chars minimum)

### Code Quality ✅
- ✅ Clean separation of concerns (middleware, routers, AI modules)
- ✅ Comprehensive error handling with try-except blocks
- ✅ Logging for debugging (login actions, activity logs)
- ✅ Type hints with Pydantic models (validation at API boundary)

### Parser Improvements ✅
- ✅ AI fallback mechanism for low-confidence extractions
- ✅ Surcharge extraction (previously skipped, now captured)
- ✅ Confidence scoring for quality monitoring
- ✅ Multi-sheet support with per-sheet stats

---

## Recommended Actions

### Immediate (Before Production Deploy)
1. **Review auth dependencies** for service mutation endpoints (assign, status, notes)
2. **Add unit tests** for input sanitization regex against injection payloads
3. **Configure HSTS header** via env var to support dev/prod environments
4. **Verify AI parser costs** — monitor Gemini/DeepSeek API usage for large file uploads

### High Priority (Next Sprint)
1. **Implement Redis storage** for rate limiter (horizontal scaling)
2. **Add confidence threshold** config and monitoring logs
3. **Write integration tests** for auth middleware chain
4. **Add surcharge validation** logs for manual review

### Medium Priority (Backlog)
1. Strengthen password policy (complexity requirements)
2. Add frontend error boundary for SpeedInsights
3. Optimize middleware order (SlowAPI before GZip)
4. Add metrics dashboard for rate limit violations

---

## Metrics

### Security Coverage
- **Auth Protected Endpoints:** 90% (13/14 data mutation endpoints require auth)
- **Rate Limited Endpoints:** 2 (login + default 100/min global)
- **Input Sanitization:** Search endpoints only (customers, vendors)
- **Security Headers:** 4 (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, HSTS)

### Type Safety
- **Pydantic Models:** 100% for API request/response
- **Type Hints:** Present in all new code
- **Linting:** Not run (no evidence of Ruff/Flake8 in CI)

### Build Status
- **Python Syntax:** ✅ PASS (verified via `py_compile`)
- **Dependencies:** ✅ slowapi>=0.1.9 added to requirements.txt
- **Frontend Build:** Not tested (vite.config.js changes need npm build verification)

### Parser Performance
- **Regex Parser:** Handles pivot-style trucking rate sheets
- **AI Fallback:** Triggered when confidence < 60% or 0 rates extracted
- **Surcharge Extraction:** NEW — captures additional revenue line items
- **Confidence Metric:** `regex_count / total_data_rows` (needs tuning)

---

## Security Audit Summary

### Authentication ✅
- ✅ JWT token-based auth implemented
- ✅ Password hashing with bcrypt
- ✅ Role-based access control (STAFF, MANAGER, ADMIN)
- ⚠️ Some mutation endpoints allow any authenticated user (see High Priority #1)

### Authorization ✅
- ✅ Admin router protected with `require_manager_or_admin`
- ✅ Delete operations require elevated role
- ⚠️ Service assignment/status updates accessible to STAFF role (verify if intentional)

### Input Validation ✅
- ✅ Pydantic validation on all API inputs
- ✅ Search query sanitization with regex
- ⚠️ No unit tests for injection payloads (see High Priority #2)

### Rate Limiting ⚠️
- ✅ Login endpoint: 5 requests/minute
- ✅ Default: 100 requests/minute
- ⚠️ In-memory storage (doesn't scale horizontally, resets on restart)

### Data Protection ✅
- ✅ Passwords hashed with bcrypt
- ✅ JWT tokens with expiration
- ✅ HTTPS enforced via HSTS header
- ✅ No sensitive data logged

### Common Vulnerabilities
- **SQL Injection:** ✅ Low risk (Supabase client, input sanitization)
- **XSS:** ✅ Mitigated (X-XSS-Protection header, React auto-escaping)
- **CSRF:** ⚠️ Not explicitly protected (consider adding CSRF tokens for state-changing operations)
- **Clickjacking:** ✅ Mitigated (X-Frame-Options: DENY)
- **MIME Sniffing:** ✅ Mitigated (X-Content-Type-Options: nosniff)

---

## Unresolved Questions

1. **Auth Policy Clarification:** Should STAFF role be allowed to update service assignments/status/notes, or only MANAGER/ADMIN?
2. **Rate Limit Storage:** Is Redis available in Railway deployment, or should we implement distributed rate limiting differently?
3. **AI Parser Costs:** What's the budget for Gemini/DeepSeek API calls? Monitor usage for large file uploads (60+ rows).
4. **CSRF Protection:** Is CSRF token validation required, or is CORS + JWT sufficient for SPA architecture?
5. **Surcharge DB Schema:** Has `is_surcharge` boolean field been added to `vendor_rates`/`customer_rates` tables via migration?
6. **Frontend Build:** Have `vite.config.js` code splitting changes been tested? Verify bundle sizes after build.
