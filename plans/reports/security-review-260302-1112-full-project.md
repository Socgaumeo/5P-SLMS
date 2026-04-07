# Security Review Report - 5P-SLMS Project

**Review Date:** 2026-03-02
**Project:** 5P-SLMS (Short-haul Logistics Management System)
**Stack:** FastAPI + React + Supabase PostgreSQL
**Deployment:** Railway (Backend) + Vercel (Frontend)

---

## Code Review Summary

### Scope
- Files reviewed: 15+ core backend/frontend files
- Lines of code analyzed: ~3,500 backend, frontend React components
- Review focus: Security vulnerabilities, authentication, authorization, SQL injection, XSS, file upload, CORS, secrets management
- Updated plans: None (review only)

### Overall Assessment
**MODERATE RISK** - Application has functional authentication but **CRITICAL authorization gaps**. Multiple admin/data modification endpoints are **completely unprotected**. SQL injection risks mitigated by Supabase client, but user input in search queries could be exploited. No rate limiting detected. Secrets management adequate but missing .env.example for documentation.

---

## CRITICAL Issues

### 1. **Missing Authentication on ALL Admin Endpoints** ⚠️ CRITICAL
**Severity:** CRITICAL
**Impact:** Complete unauthorized access to master data CRUD operations

**Finding:**
ALL admin endpoints in `/api/admin/*` have **ZERO authentication/authorization checks**:
- Service types CRUD
- Vendors CRUD
- Customers CRUD
- Selling rates CRUD
- Buying rates CRUD
- Routes CRUD
- Cost items CRUD
- Vendor rates summary/detail

**Vulnerable Code (admin.py):**
```python
@router.get("/service-types")
def list_service_types(...):  # NO AUTHENTICATION
    ...

@router.post("/vendors")
def create_vendor(data: VendorCreate):  # NO AUTHENTICATION
    ...

@router.delete("/customers/{customer_id}")
def delete_customer(customer_id: int, hard_delete: bool):  # NO AUTHENTICATION
    ...
```

**Impact:**
- Anonymous users can read/create/update/delete ALL master data
- Financial data (rates, prices) exposed
- Business-critical vendor/customer info can be wiped
- Hard deletes allowed without auth

**Fix Required:**
```python
from app.api.dependencies import require_admin

@router.post("/vendors", dependencies=[Depends(require_admin)])
def create_vendor(data: VendorCreate):
    ...

@router.delete("/customers/{customer_id}", dependencies=[Depends(require_admin)])
def delete_customer(customer_id: int, hard_delete: bool):
    ...
```

---

### 2. **Missing Authentication on Core Job/Service Endpoints** ⚠️ CRITICAL
**Severity:** CRITICAL
**Impact:** Unauthorized job/service manipulation

**Finding:**
Main.py endpoints lack authentication:
- `/api/services/{svc_id}/assign` - Assign vendors/vehicles (PUT)
- `/api/services/{svc_id}/status` - Update service status (PUT)
- `/api/services/{svc_id}` - Delete service (DELETE)
- `/api/services/{svc_id}/notes` - Update notes (PUT)
- `/api/jobs/{job_id}/status` - Update job status (PUT)
- `/api/jobs/{job_id}/cancel` - Cancel job (DELETE)
- `/api/dashboard/stats` - Dashboard stats (GET)
- `/api/customers` - List customers (GET)
- `/api/vendors` - List vendors (GET)
- `/api/employees` - List employees (GET)

**Vulnerable Code (main.py lines 212-460):**
```python
@app.put("/api/services/{svc_id}/assign")
async def assign_service(svc_id: int, request: AssignServiceRequest):
    # NO AUTH CHECK - anyone can assign vendors/vehicles
    ...

@app.delete("/api/jobs/{job_id}/cancel")
async def cancel_job(job_id: int):
    # NO AUTH CHECK - anyone can cancel any job
    ...
```

**Fix Required:**
```python
from app.api.dependencies import get_current_user

@app.put("/api/services/{svc_id}/assign")
async def assign_service(
    svc_id: int,
    request: AssignServiceRequest,
    current_user: dict = Depends(get_current_user)
):
    # Verify user has permission to modify this service
    ...
```

---

### 3. **Rate File Upload - No Authentication** ⚠️ HIGH
**Severity:** HIGH
**Impact:** Unauthorized rate data manipulation

**Finding:**
`/api/admin/rates/upload-file` and `/api/admin/rates/confirm-import` have NO authentication.

**Vulnerable Code (rate_file_upload.py):**
```python
@router.post("/upload-file")
async def upload_rate_file(
    file: UploadFile = File(...),
    rate_type: str = Form("buying"),
    vendor_id: Optional[int] = Form(None),
    ...
):
    # NO AUTH - anyone can upload rate files
```

**Impact:**
- Anonymous users can upload malicious Excel files
- Bulk import fake/manipulated rates
- Potential path traversal via filename
- No file size limits detected

**Fix Required:**
Add authentication + file validation:
```python
@router.post("/upload-file", dependencies=[Depends(require_admin)])
async def upload_rate_file(...):
    # Validate file size
    if file.size > 10_000_000:  # 10MB limit
        raise HTTPException(400, "File too large")

    # Sanitize filename
    safe_filename = secure_filename(file.filename)
    ...
```

---

### 4. **SQL Injection Risk in Search Queries** ⚠️ MEDIUM-HIGH
**Severity:** MEDIUM-HIGH
**Impact:** Potential SQL injection via user search input

**Finding:**
User input directly interpolated into `.ilike()` and `.or_()` filters without sanitization.

**Vulnerable Code (main.py lines 135, 165):**
```python
# /api/search/customers
search_filter = f"customer_code.ilike.%{q}%,short_name.ilike.%{q}%,company_name.ilike.%{q}%"
result = client.table('customers').select(...).or_(search_filter).execute()

# /api/search/vendors
search_filter = f"vendor_code.ilike.%{q}%,short_name.ilike.%{q}%,company_name.ilike.%{q}%"
result = client.table('vendors').select(...).or_(search_filter).execute()
```

**Also in:**
- admin.py lines 272-275 (vendors search)
- admin.py lines 389-393 (customers search)
- admin.py lines 1016-1019 (cost items search)
- users.py lines 77-80 (users search)

**Impact:**
- User input `q` parameter directly interpolated
- PostgREST filters could be exploited with special characters
- Potential data exfiltration if attacker crafts malicious queries

**Mitigation:**
Supabase Python client provides some protection, but **sanitize user input**:
```python
import re

def sanitize_search(q: str) -> str:
    # Remove special PostgREST characters
    return re.sub(r'[,.()*]', '', q).strip()

q_safe = sanitize_search(q)
search_filter = f"customer_code.ilike.%{q_safe}%,..."
```

---

### 5. **Missing CSRF Protection** ⚠️ MEDIUM
**Severity:** MEDIUM
**Impact:** Cross-site request forgery attacks

**Finding:**
No CSRF tokens detected for state-changing operations (POST/PUT/DELETE).

**Risk:**
- Attacker can craft malicious forms that submit to API endpoints
- If user is authenticated, requests will succeed
- Especially dangerous for unprotected admin endpoints

**Fix Required:**
Add CSRF middleware or require custom headers:
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.csrf import CSRFMiddleware  # if available

app.add_middleware(
    CSRFMiddleware,
    secret_key=settings.SECRET_KEY
)
```

Or require custom header:
```python
async def verify_csrf_header(request: Request):
    if request.method in ["POST", "PUT", "DELETE"]:
        if request.headers.get("X-Requested-With") != "XMLHttpRequest":
            raise HTTPException(403, "Invalid request")
```

---

### 6. **Supabase Service Role Key Usage** ⚠️ MEDIUM
**Severity:** MEDIUM
**Impact:** Bypasses Row Level Security (RLS)

**Finding:**
All backend queries use `SUPABASE_SERVICE_ROLE_KEY` (supabase_client.py line 30).

**Vulnerable Code:**
```python
def get_supabase() -> Client:
    _supabase_client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY  # BYPASSES RLS
    )
```

**Impact:**
- Service role key bypasses ALL Row Level Security policies
- If backend is compromised, attacker has full DB access
- No database-level permission checks

**Best Practice:**
- Use anon key + RLS for read operations
- Use service role ONLY for admin operations
- Implement RLS policies in Supabase
- Pass user JWT to Supabase for per-user access control

**Current Implementation:**
Backend does authentication in code, not at DB level. This is acceptable IF all endpoints are properly protected (which they currently are NOT).

---

## HIGH Priority Findings

### 7. **No Rate Limiting** ⚠️ HIGH
**Severity:** HIGH
**Impact:** API abuse, DDoS, brute force attacks

**Finding:**
No rate limiting middleware detected on any endpoint.

**Risk:**
- Brute force password attacks on `/api/auth/login`
- API abuse on search endpoints
- File upload spam
- Resource exhaustion

**Fix Required:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/auth/login")
@limiter.limit("5/minute")
async def login(...):
    ...
```

---

### 8. **Weak Password Policy** ⚠️ HIGH
**Severity:** HIGH
**Impact:** Account compromise

**Finding:**
Minimum password length is only 6 characters (auth.py line 212).

**Vulnerable Code:**
```python
if len(new_password) < 6:
    raise HTTPException(400, detail="Mật khẩu mới phải có ít nhất 6 ký tự")
```

**Best Practice:**
- Minimum 8-12 characters
- Require mix of uppercase/lowercase/numbers/symbols
- Check against common password lists
- Implement password strength meter

**Fix:**
```python
import re

def validate_password(password: str):
    if len(password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters")
    if not re.search(r'[A-Z]', password):
        raise HTTPException(400, "Password must contain uppercase letter")
    if not re.search(r'[a-z]', password):
        raise HTTPException(400, "Password must contain lowercase letter")
    if not re.search(r'\d', password):
        raise HTTPException(400, "Password must contain number")
```

---

### 9. **JWT Secret Key Validation** ⚠️ HIGH
**Severity:** HIGH
**Impact:** Token forgery if weak secret

**Finding:**
JWT_SECRET_KEY validation only in production (config.py line 56).

**Vulnerable Code:**
```python
@model_validator(mode='after')
def validate_required_secrets(self):
    if not self.DEBUG:  # Only validates in production
        if not self.JWT_SECRET_KEY:
            missing.append("JWT_SECRET_KEY")
```

**Risk:**
- Development environments may use weak/default secrets
- Secrets could leak to git if DEBUG=True
- No minimum length check

**Fix:**
```python
@model_validator(mode='after')
def validate_jwt_secret(self):
    if self.JWT_SECRET_KEY:
        if len(self.JWT_SECRET_KEY) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
    elif not self.DEBUG:
        raise ValueError("JWT_SECRET_KEY required for production")
    return self
```

---

### 10. **Missing .env.example File** ⚠️ MEDIUM
**Severity:** MEDIUM
**Impact:** Developer onboarding, accidental secret exposure

**Finding:**
No `.env.example` file exists in backend/.

**Risk:**
- New developers don't know what env vars are required
- May commit actual .env file
- No documentation of expected secrets

**Fix Required:**
Create `backend/.env.example`:
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
SUPABASE_ANON_KEY=your_anon_key_here

# AI Configuration
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_key_here
GOOGLE_GEMINI_API_KEY=your_gemini_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Security
SECRET_KEY=change_this_to_random_string_min_32_chars
JWT_SECRET_KEY=change_this_to_random_string_min_32_chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480

# CORS
ALLOWED_ORIGINS=http://localhost:5173,https://yourdomain.com

# Environment
DEBUG=False
```

---

## MEDIUM Priority Improvements

### 11. **CORS Configuration Too Permissive** ⚠️ MEDIUM
**Severity:** MEDIUM
**Impact:** Potential CSRF attacks

**Finding:**
CORS allows ALL methods and ALL headers (main.py lines 43-44).

**Vulnerable Code:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[...],
    allow_credentials=True,
    allow_methods=["*"],  # Too permissive
    allow_headers=["*"],  # Too permissive
)
```

**Best Practice:**
Restrict to required methods/headers:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[...],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["Content-Disposition"],
)
```

---

### 12. **Database URL Logging** ⚠️ MEDIUM
**Severity:** MEDIUM
**Impact:** Credentials exposure in logs

**Finding:**
Database URL logged at startup (main.py line 25).

**Vulnerable Code:**
```python
logger.info(f"📊 Database: {settings.DATABASE_URL[:50]}...")
```

**Risk:**
- If DATABASE_URL contains credentials, they're logged
- Logs may be stored in plaintext
- Could leak to monitoring systems

**Fix:**
```python
from urllib.parse import urlparse

db_parsed = urlparse(settings.DATABASE_URL)
safe_db_url = f"{db_parsed.scheme}://{db_parsed.hostname}:{db_parsed.port}/{db_parsed.path}"
logger.info(f"📊 Database: {safe_db_url}")
```

---

### 13. **No Input Validation on File Names** ⚠️ MEDIUM
**Severity:** MEDIUM
**Impact:** Path traversal attacks

**Finding:**
File upload endpoints don't sanitize filenames (rate_file_upload.py, chat.py).

**Vulnerable Code:**
```python
file_name = os.path.basename(file_path)  # Not sufficient
ext = os.path.splitext(file.filename or "")[1].lower()
```

**Risk:**
- Malicious filenames: `../../etc/passwd`
- Special characters breaking file operations
- Directory traversal

**Fix:**
```python
import re
from werkzeug.utils import secure_filename

def sanitize_filename(filename: str) -> str:
    # Remove path components
    filename = os.path.basename(filename)
    # Use werkzeug's secure_filename
    filename = secure_filename(filename)
    # Additional sanitization
    filename = re.sub(r'[^\w\s\.-]', '', filename)
    return filename[:255]  # Limit length

safe_name = sanitize_filename(file.filename)
```

---

### 14. **Error Messages Leak Implementation Details** ⚠️ LOW-MEDIUM
**Severity:** LOW-MEDIUM
**Impact:** Information disclosure

**Finding:**
Error messages expose internal details (main.py line 107, admin.py multiple locations).

**Examples:**
```python
return {"customers": [], "error": str(e)}  # Exposes full exception
logger.error(f"List customers error: {e}")
import traceback
logger.error(traceback.format_exc())  # Full stack trace in logs
```

**Risk:**
- Attackers learn about internal structure
- Database errors reveal schema info
- File paths exposed

**Best Practice:**
```python
try:
    ...
except Exception as e:
    logger.error(f"List customers error: {e}", exc_info=True)
    # Return generic error to user
    return {"customers": [], "error": "An error occurred. Please try again."}
```

---

### 15. **Missing Security Headers** ⚠️ LOW-MEDIUM
**Severity:** LOW-MEDIUM
**Impact:** XSS, clickjacking, MIME sniffing attacks

**Finding:**
No security headers middleware detected.

**Missing Headers:**
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security (HSTS)
- Content-Security-Policy (CSP)

**Fix Required:**
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

## LOW Priority Suggestions

### 16. **No dangerouslySetInnerHTML Found** ✅ GOOD
**Severity:** N/A
**Finding:** No XSS vulnerabilities via `dangerouslySetInnerHTML` detected in frontend React components.

---

### 17. **Frontend Dependencies - No Vulnerabilities** ✅ GOOD
**Severity:** N/A
**Finding:** `npm audit` found 0 vulnerabilities in frontend dependencies.

---

### 18. **Password Hashing Uses bcrypt** ✅ GOOD
**Severity:** N/A
**Finding:** Passwords properly hashed with bcrypt (security.py lines 29-34).

---

### 19. **.env Files Properly Ignored** ✅ GOOD
**Severity:** N/A
**Finding:** `.gitignore` includes `.env` and `.env.local` (lines 1-2).

---

### 20. **JWT Implementation Correct** ✅ GOOD
**Severity:** N/A
**Finding:** JWT tokens properly signed with HS256, expiration set to 8 hours (security.py).

---

## Positive Observations

1. **Authentication logic is sound** - JWT implementation is correct, password hashing uses bcrypt
2. **Dependencies are up-to-date** - No known vulnerabilities in npm packages
3. **Environment secrets properly excluded** - .gitignore correctly configured
4. **Supabase client usage** - PostgREST provides some SQL injection protection
5. **Pydantic validation** - Request models provide basic input validation
6. **Role-based permission system exists** - `check_permission()` function in dependencies.py (just not used)
7. **Activity logging present** - Login/logout actions logged to `activity_logs` table

---

## Recommended Actions (Prioritized)

### IMMEDIATE (Must Fix Before Production)

1. **Add authentication to ALL `/api/admin/*` endpoints**
   - Use `dependencies=[Depends(require_admin)]` on all admin routes
   - Estimated effort: 2-3 hours

2. **Add authentication to job/service modification endpoints in main.py**
   - Protect all PUT/DELETE operations
   - Estimated effort: 1-2 hours

3. **Implement rate limiting**
   - Use slowapi library
   - Apply to login, search, file upload endpoints
   - Estimated effort: 1 hour

4. **Sanitize search query input**
   - Add input sanitization function
   - Apply to all `.ilike()` queries
   - Estimated effort: 1 hour

5. **Add CSRF protection**
   - Require custom header or implement CSRF tokens
   - Estimated effort: 2 hours

### HIGH PRIORITY (Within 1 Week)

6. **Strengthen password policy**
   - Minimum 8 characters, complexity requirements
   - Estimated effort: 1 hour

7. **Add security headers middleware**
   - Implement middleware function
   - Estimated effort: 30 minutes

8. **Fix database URL logging**
   - Sanitize logged URLs
   - Estimated effort: 15 minutes

9. **Add file upload validation**
   - File size limits, filename sanitization
   - Estimated effort: 1 hour

10. **Create .env.example file**
    - Document all required environment variables
    - Estimated effort: 30 minutes

### MEDIUM PRIORITY (Within 2 Weeks)

11. **Restrict CORS configuration**
    - Limit allowed methods/headers
    - Estimated effort: 15 minutes

12. **Improve error handling**
    - Return generic errors to users
    - Log detailed errors server-side only
    - Estimated effort: 2 hours

13. **Implement RLS in Supabase**
    - Define row-level security policies
    - Migrate from service role to user-scoped queries
    - Estimated effort: 4-6 hours

14. **Add request logging**
    - Log all API requests for audit trail
    - Estimated effort: 1 hour

### LOW PRIORITY (Nice to Have)

15. **Add API documentation with security notes**
16. **Implement session management (token blacklist)**
17. **Add 2FA support for admin accounts**
18. **Implement IP whitelisting for admin routes**
19. **Add automated security testing in CI/CD**

---

## Metrics

- **Type Coverage:** N/A (Python FastAPI project)
- **Test Coverage:** Not evaluated (no tests reviewed)
- **Linting Issues:** Not evaluated
- **Critical Security Issues:** 6 (auth bypass, SQL injection, rate limiting, CSRF, service role usage, weak password)
- **High Priority Issues:** 4 (rate limiting, password policy, JWT secret, .env.example)
- **Medium Priority Issues:** 5 (CORS, logging, file validation, error messages, security headers)
- **Low Priority Issues:** 0
- **Positive Security Practices:** 6

---

## Summary

**Total Issues Found:** 15 security concerns
**Severity Breakdown:**
- Critical: 6
- High: 4
- Medium: 5
- Low: 0

**Estimated Total Fix Time:** 15-20 hours for all critical and high priority items

**Deployment Recommendation:** **DO NOT deploy to production** until critical authentication issues are resolved. Current state allows complete unauthorized access to admin functions and data modification.

**Next Steps:**
1. Apply IMMEDIATE fixes (authentication on all endpoints)
2. Add rate limiting
3. Deploy to staging for security testing
4. Conduct penetration testing
5. Fix remaining HIGH/MEDIUM issues
6. Deploy to production with monitoring

---

## Unresolved Questions

1. **Are there RLS policies already configured in Supabase?** - If yes, backend should use anon key for some operations
2. **Is there a separate admin dashboard?** - If yes, it should be on a separate subdomain with IP whitelist
3. **What is the expected traffic volume?** - Affects rate limiting configuration
4. **Are there any security compliance requirements?** (GDPR, PCI-DSS, etc.)
5. **Is there a Web Application Firewall (WAF)?** - Railway may provide some protection
6. **Are there automated backups configured in Supabase?** - Critical for data protection
7. **Is there a disaster recovery plan?** - Important for business continuity
8. **Are API keys rotated regularly?** - Best practice for long-running systems

---

**Report Generated:** 2026-03-02 11:18 UTC
**Reviewer:** Claude Code (Security Review Agent)
**Project Path:** /Users/bear1108/Documents/GitHub/5P-SLMS
