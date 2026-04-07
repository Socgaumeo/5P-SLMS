# Code Maintenance & Stability Research Report
**Date:** 2026-03-06
**Project:** 5P SLMS (FastAPI/React/Supabase)
**Team Size:** 1-3 developers

## Executive Summary
Production stability for small teams requires **automation-first** approach—prioritize easy-win tooling that prevents rollbacks. Current setup has minimal CI/CD; focus on quick wins: health checks, automated tests, error monitoring.

---

## 1. Testing Strategy (FastAPI)

### Recommended Stack
- **pytest** + **httpx** for async API testing
- **pytest-cov** for coverage tracking (target: 70%+ for critical paths)
- **conftest.py** for shared fixtures (auth, DB mocks)

### Quick Implementation
```python
# backend/tests/conftest.py
@pytest.fixture
async def client():
    return AsyncClient(app=app, base_url="http://test")

# Tests for each router (health, auth, jobs)
```

### Current Gap
- No automated test runs in CI/CD pipeline
- Tests are manual/integration-only

### Action
Add to `.github/workflows/`: `pytest backend/ --cov=app --cov-fail-under=70`

---

## 2. CI/CD Pipeline Improvements

### Priority 1: Add Test Gate (1 hour)
Current workflow deploys on every main push. Add:
- Linting check (ruff)
- Type check (mypy)
- Test suite (pytest)
- Dependency scan (Safety)

### Priority 2: Staging Deployment
Separate workflow for PR validation before main merge.

### Cost-Benefit
- Prevents ~90% of rollbacks
- Catches syntax errors, type issues, missing imports before production

---

## 3. Error Monitoring & Logging

### Minimal Setup (Free Tier)
**Sentry** (5K events/month free):
```python
import sentry_sdk
sentry_sdk.init("https://key@sentry.io/123", traces_sample_rate=0.1)
```

**LogRocket** (React, 50K sessions/month free)

### Logging Pattern (FastAPI)
```python
# app/core/logging.py
logging.basicConfig(
    level="INFO",
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
# Use structured logs: logger.info("action", extra={"user_id": uid})
```

### Current Gap
- No centralized error tracking
- App crashes silently or cause silent failures

---

## 4. Dependency Management

### Tools
- **Dependabot** (GitHub native, free): Auto-creates PRs for dep updates
- **Safety**: `pip install safety && safety check` in CI
- **pip-audit**: Similar to Safety, detects CVEs

### Quick Setup
GitHub UI → Settings → Code Security → Enable Dependabot alerts

---

## 5. Database Migration Safety

### Current Setup
- Using SQLAlchemy ORM (good)
- Manual scripts in `backend/scripts/` (risky)

### Recommendation: Alembic
```bash
# Init
alembic init alembic

# Create migration
alembic revision --autogenerate -m "add column"

# Deploy
alembic upgrade head
```

### Safety Rules
- Always test migrations on staging
- Include rollback scripts
- Keep migrations small (single logical change)
- Never lock tables in production

---

## 6. API Versioning & Backward Compatibility

### Approach (KISS)
Use URL versioning: `/api/v1/jobs` → `/api/v2/jobs` if breaking changes

### Deprecation Pattern
```python
@app.get("/api/v1/jobs")  # Old endpoint
async def jobs_v1():
    logger.warning("v1 endpoint deprecated; use v2")
    return await jobs_v2()

@app.get("/api/v2/jobs")  # New endpoint
async def jobs_v2():
    pass
```

### Current Gap
Single `/api/*` path; no versioning strategy

---

## 7. Health Checks & Uptime Monitoring

### Endpoint (Already Exists)
`backend/app/api/health.py` returns system status. Enhance:

```python
@app.get("/health/live")  # K8s liveness
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")  # K8s readiness
async def readiness():
    try:
        # Check DB connection
        await db.execute("SELECT 1")
        return {"status": "ready"}
    except:
        return {"status": "unhealthy"}, 503
```

### Monitoring
- **Uptime Robot** (free): Ping `/health/live` every 5 min
- **Railway alerts**: Configure email on deployment failure

---

## 8. Code Quality Tools

### Quick Stack (30 min setup)
```bash
pip install ruff mypy pytest pytest-cov black

# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### Run: `pre-commit install && pre-commit run --all-files`

---

## 9. Performance Monitoring

### Minimal Setup
- **Prometheus metrics** in FastAPI (prometheus-client)
- **Response time logging**: Auto-tracked via middleware
- **Database query logging**: SQLAlchemy `echo=True` in dev, logs in prod

### Key Metrics
- API response time (p50, p95, p99)
- Database query count per request
- Error rate (5xx responses)
- Rate limit hit rate

---

## 10. Deployment Checklist

### Pre-Deploy
- [ ] Tests pass (`pytest backend/`)
- [ ] Linting clean (`ruff check backend/`)
- [ ] Type check passes (`mypy backend/`)
- [ ] No security vulnerabilities (`safety check`)
- [ ] Database migrations tested on staging

### Post-Deploy
- [ ] Health check responds (5 min)
- [ ] No critical errors in Sentry (10 min)
- [ ] Response times normal (<500ms p95)
- [ ] User reports no issues (first hour)

---

## Implementation Roadmap

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| P1 | Add pytest + CI gate | 2h | Prevents 90% rollbacks |
| P1 | Add Sentry monitoring | 1h | Visibility on errors |
| P1 | Health checks (readiness) | 30m | Uptime monitoring |
| P2 | Dependabot + Safety | 30m | Security alerts |
| P2 | pre-commit hooks | 1h | Code quality automation |
| P3 | Alembic migrations | 3h | Safe DB changes |
| P3 | API versioning schema | 2h | Future-proofs API |

---

## Unresolved Questions

1. **Staging environment**: Is Railway configured for staging deploys? (Needed for safe testing)
2. **Database backups**: Current backup strategy for Supabase?
3. **Secrets management**: How are API keys rotated (Anthropic, Gemini, DeepSeek)?
4. **Rollback procedure**: What's the manual rollback process if deployment fails?
5. **Alert recipients**: Who gets notified on Sentry errors / failed deployments?

---

## Quick-Win Checklist (This Week)

- [ ] Add `pytest` tests for 3 critical routes (auth, jobs, chat)
- [ ] Add GitHub Actions step: `pytest && ruff check`
- [ ] Set up Sentry SDK integration
- [ ] Create `/health/ready` endpoint with DB check
- [ ] Enable Dependabot alerts
- [ ] Document deploy checklist for team
