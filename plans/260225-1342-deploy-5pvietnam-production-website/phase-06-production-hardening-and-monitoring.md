# Phase 06: Production Hardening & Monitoring

## Context Links

- [plan.md](plan.md) - Overview
- [phase-01](phase-01-prepare-production-configs.md) - Config changes
- [backend/main.py](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/main.py) - FastAPI app

## Overview

- **Priority**: P2
- **Status**: pending
- **Effort**: 30m
- **Description**: Add security headers, HTTPS redirect, structured logging, and basic monitoring to production backend

## Key Insights

- FastAPI middleware handles security headers and HTTPS redirect
- Railway provides basic monitoring (CPU, RAM, logs) in dashboard
- Supabase dashboard has DB monitoring (query performance, connections)
- No need for external APM (Datadog, Sentry) in MVP - add if issues arise
- Vercel provides frontend analytics for free

## Requirements

### Functional
- Security headers on all backend responses (X-Content-Type-Options, etc.)
- HTTPS redirect for backend (if Railway doesn't handle it)
- Structured JSON logging for production
- Health check monitoring (can use free UptimeRobot)

### Non-Functional
- No performance regression from middleware
- Logs parseable by Railway log viewer
- Monitoring alerts within 5min of downtime

## Architecture

```
Request Flow with Hardening:
Client --> HTTPS (Vercel/Railway auto)
       --> Security Headers Middleware
       --> CORS Middleware (already configured)
       --> FastAPI Router
       --> Response with security headers

Monitoring:
UptimeRobot (free) --> /health every 5min
Railway Dashboard --> CPU, RAM, logs
Supabase Dashboard --> DB connections, queries
```

## Related Code Files

### Files to Modify
- `backend/main.py` - Add security headers middleware, structured logging

### Files to Create
- `backend/app/middleware/security-headers-middleware.py` - Security headers middleware

## Implementation Steps

### 1. Create Security Headers Middleware

Create `backend/app/middleware/security-headers-middleware.py`:

```python
"""Security headers middleware for production"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if not request.url.path.startswith("/docs"):
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response
```

### 2. Update `backend/main.py` - Add Middleware

Add after CORS middleware:

```python
from app.middleware.security_headers_middleware import SecurityHeadersMiddleware

# Security headers (production only)
if not settings.DEBUG:
    app.add_middleware(SecurityHeadersMiddleware)
```

### 3. Configure Structured Logging

Update logging setup in `backend/main.py`:

```python
import json
import sys

if settings.DEBUG:
    logging.basicConfig(level=logging.INFO)
else:
    # JSON structured logging for production
    logging.basicConfig(
        level=logging.INFO,
        format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
        stream=sys.stdout
    )
```

### 4. Add HTTPS Redirect Middleware (Backend)

Railway auto-handles HTTPS redirect, but add a safety layer:

```python
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

if not settings.DEBUG:
    app.add_middleware(HTTPSRedirectMiddleware)
```

**Note**: Test this carefully. Railway may already redirect HTTP->HTTPS at the load balancer level. If double-redirect occurs, remove this middleware.

### 5. Setup Free Uptime Monitoring

1. Go to [uptimerobot.com](https://uptimerobot.com) (free tier: 50 monitors, 5-min interval)
2. Create account
3. Add monitors:

| Monitor | URL | Interval | Alert |
|---------|-----|----------|-------|
| Frontend | `https://5pvietnam.com` | 5 min | Email |
| Backend Health | `https://api.5pvietnam.com/health` | 5 min | Email |
| Backend DB | `https://api.5pvietnam.com/health/db` | 15 min | Email |

4. Set alert contacts (email, optional Telegram/Slack webhook)

### 6. Verify Supabase Monitoring

1. Go to Supabase Dashboard > Project > Database
2. Check "Database Health" section
3. Monitor connection pool usage
4. Set up Supabase email alerts if available

### 7. Add Vercel Security Headers (Frontend)

Update `frontend/vercel.json`:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```

### 8. Backup Strategy Verification

Supabase free tier includes daily backups. Verify:
1. Supabase Dashboard > Project > Settings > Database
2. Confirm "Point in Time Recovery" or daily backups enabled
3. For Pro plan: backups retained for 7 days

No additional backup setup needed - Supabase handles it.

## Todo List

- [ ] Create security headers middleware file
- [ ] Add security headers middleware to `main.py`
- [ ] Configure structured JSON logging for production
- [ ] Test HTTPS redirect behavior on Railway (add middleware only if needed)
- [ ] Update `frontend/vercel.json` with security headers
- [ ] Setup UptimeRobot monitors (frontend + backend health)
- [ ] Verify Supabase backup configuration
- [ ] Run full E2E test with all hardening in place
- [ ] Monitor Railway dashboard for resource usage post-deploy

## Success Criteria

- Response headers include X-Content-Type-Options, X-Frame-Options, etc.
- Backend logs output valid JSON in production
- UptimeRobot shows green status for all monitors
- Security headers visible in browser DevTools > Network > Response Headers
- No CSP violations on frontend (check browser console)
- Supabase backups confirmed active

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| HTTPS redirect loop | Medium | High | Test on Railway first; remove if double-redirect |
| CSP blocks legitimate requests | Medium | Medium | Exclude `/docs` endpoint; test thoroughly |
| Structured logging breaks log parsing | Low | Low | Test locally before deploying |
| Security headers break CORS | Low | High | Security headers added AFTER CORS middleware |

## Security Considerations

- **Headers**: Defense-in-depth; not a replacement for proper auth/CORS
- **CSP**: Start permissive, tighten iteratively
- **HTTPS**: Enforced at platform level (Vercel/Railway) + middleware backup
- **Monitoring**: Alerts on downtime; manual investigation for security incidents
- **Backups**: Supabase-managed; verify retention policy matches needs

## Next Steps

- Post-launch: Monitor for 48h, check error logs
- Future iteration: Add Sentry for error tracking if needed
- Future iteration: Add rate limiting with fastapi-limiter + Upstash Redis
- Future iteration: Add WAF rules if attack patterns emerge
