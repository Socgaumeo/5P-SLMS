# Phase 3: Backend Production Hardening

## Context Links
- [Research: CI/CD & Security](research/researcher-02-cicd-security.md)
- [Backend config.py](../../backend/app/core/config.py)
- [Backend main.py](../../backend/main.py)
- [Backend gunicorn_conf.py](../../backend/gunicorn_conf.py)

## Overview
- **Priority**: P1 (security-critical)
- **Status**: pending
- **Effort**: 1.5h
- **Description**: Harden FastAPI backend for production: security headers, rate limiting, CORS lockdown, logging, input validation

## Key Insights
- CORS currently uses `allow_methods=["*"]` and `allow_headers=["*"]` -- should restrict in production
- No security headers middleware exists yet
- No rate limiting exists yet
- Pydantic config already validates required secrets when DEBUG=False (good)
- Gunicorn set to 1 worker due to in-memory conversation state (acceptable for small team)
- `main.py` is 460 lines; consider extracting inline endpoints to proper router modules (separate concern)

## Requirements

### Functional
- Security headers added to all responses
- Rate limiting on sensitive endpoints (auth, chat)
- CORS restricted to production origins only
- Health check endpoint accessible without auth
- Structured logging for production debugging

### Non-Functional
- Response latency overhead from middleware < 5ms
- No breaking changes to existing API contracts

## Architecture

```
Request Flow (production):

Client → HTTPS → Railway reverse proxy
  → Security Headers Middleware
  → Rate Limit Middleware (slowapi)
  → CORS Middleware
  → FastAPI Router
  → Supabase PostgreSQL
```

## Related Code Files

### Files to Modify
- `backend/main.py` - Add security headers middleware, update CORS config
- `backend/requirements.txt` - Add `slowapi` dependency
- `backend/app/core/config.py` - Add RATE_LIMIT config option (optional)

### Files to Create
- `backend/app/middleware/security-headers-middleware.py` - Security headers middleware
- `backend/app/middleware/__init__.py` - Package init
- `backend/app/middleware/rate-limit-middleware.py` - Rate limiting setup

## Implementation Steps

### 1. Add Security Headers Middleware

Create `backend/app/middleware/security-headers-middleware.py`:
```python
"""Security headers middleware for production"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        return response
```

### 2. Add Rate Limiting

Add to `backend/requirements.txt`:
```
slowapi>=0.1.9
```

Create `backend/app/middleware/rate-limit-middleware.py`:
```python
"""Rate limiting configuration using slowapi"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

Apply to sensitive endpoints in `main.py`:
```python
from app.middleware.rate_limit_middleware import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

Then on auth/chat routers, add `@limiter.limit("30/minute")` decorators.

### 3. Tighten CORS in main.py

Update the CORS middleware in `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)
```

### 4. Register Security Middleware in main.py

Add after CORS middleware (order matters: security headers wrap everything):
```python
from app.middleware.security_headers_middleware import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)
```

**Middleware execution order** (outermost first):
1. SecurityHeadersMiddleware (adds headers to all responses)
2. CORSMiddleware (handles preflight + origin check)
3. Route handlers

### 5. Production Logging

Update logging in `main.py`:
```python
import logging

log_level = logging.DEBUG if settings.DEBUG else logging.INFO
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
```

### 6. Verify Production Config Validation

Current `config.py` already validates DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY when DEBUG=False. No changes needed here -- just ensure all env vars are set on Railway (Phase 1).

## Todo List
- [ ] Create `backend/app/middleware/__init__.py`
- [ ] Create security headers middleware
- [ ] Add `slowapi` to requirements.txt
- [ ] Create rate limiting setup module
- [ ] Update CORS to explicit methods/headers in main.py
- [ ] Register security headers middleware in main.py
- [ ] Register rate limiter in main.py
- [ ] Update logging format for production
- [ ] Test: verify security headers in response (`curl -I`)
- [ ] Test: verify rate limiting triggers on rapid requests
- [ ] Test: verify CORS rejects unauthorized origins
- [ ] Deploy to Railway and verify

## Success Criteria
- `curl -I https://api.5pvietnam.com/` shows security headers (X-Frame-Options, HSTS, etc.)
- Rapid requests (>30/min) to auth endpoints return 429 Too Many Requests
- Requests from `http://evil.com` are rejected by CORS
- `https://api.5pvietnam.com/docs` still accessible for API documentation
- No regressions in existing API functionality

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Rate limiter blocks legitimate traffic | Low | Medium | Set generous limits (30/min for auth, 100/min for general) |
| Middleware ordering breaks CORS preflight | Medium | High | Test OPTIONS requests; CORS must be inner middleware |
| Security headers break iframe embeds | Low | Low | X-Frame-Options: DENY is intentional; no iframe use case |

## Security Considerations
- **HSTS**: 1-year max-age with includeSubDomains; ensures all traffic over HTTPS
- **CSP**: Not added initially to avoid breaking frontend; add later if needed
- **Rate limiting**: In-memory by default (fine for 1 worker); use Redis if scaling to multiple workers
- **Secrets**: All validated at startup by Pydantic; app refuses to start without them
- **Database**: Using pooled connection (port 6543) through Supabase PgBouncer; SSL enforced

## Next Steps
- After hardening: proceed to Phase 4 (Frontend Production Build)
- Consider adding Sentry SDK for error tracking (Phase 5)
- Monitor rate limit hits in logs to tune thresholds
