# CI/CD Pipeline, Security & Production Best Practices Research

**Research Date:** 2026-03-02
**Focus:** FastAPI + React/Vite production deployment for 5P Vietnam SLMS

## 1. GitHub Actions CI/CD

### Monorepo Strategy (Recommended)
- **Path filtering**: Detect changes in `frontend/`, `backend/`, `shared/` - only build affected components
- **Separate CI from CD**: Validation workflows distinct from deployment workflows
- **Smart caching**: Cache `node_modules`, Vite cache, Python dependencies - reduces build time ~70%
- **Concurrency control**: Cancel stale runs to save Actions minutes

### Workflow Structure
```yaml
# Separate workflows recommended:
- .github/workflows/backend-ci.yml   # FastAPI tests, lint
- .github/workflows/frontend-ci.yml  # React build, tests
- .github/workflows/deploy.yml       # Deployment only (triggered after CI passes)
```

### Performance Optimizations
- Matrix builds for testing across Node/Python versions
- Turbo caching for monorepo builds
- Artifact caching between workflow runs
- `dist/` is default Vite build output

**Sources:**
- [GitHub Actions Monorepo Guide 2026](https://dev.to/pockit_tools/github-actions-in-2026-the-complete-guide-to-monorepo-cicd-and-self-hosted-runners-1jop)
- [Complete GitHub Actions CI/CD Guide](https://devtoolbox.dedyn.io/blog/github-actions-cicd-complete-guide)
- [FastAPI GitHub Actions](https://medium.com/@hasansajedi/fastapi-and-github-actions-67d86c1e6c5f)

---

## 2. Environment Variables & Secrets Management

### GitHub Secrets Setup
Store in repo Settings > Secrets and variables > Actions:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` (use Service Role key for backend admin operations)
- `ANTHROPIC_API_KEY`
- `GOOGLE_GEMINI_API_KEY`
- `DEEPSEEK_API_KEY`
- `DATABASE_URL` (Supabase connection string)

### FastAPI Best Practices
- **Pydantic BaseSettings**: Validate env vars at startup
  ```python
  from pydantic_settings import BaseSettings

  class Settings(BaseSettings):
      SUPABASE_URL: str
      SUPABASE_SERVICE_ROLE_KEY: str
      # ... other secrets

      class Config:
          env_file = ".env"  # Only for local dev
  ```
- **Never commit `.env`** to version control
- **Production**: Inject secrets via platform env vars (no `.env` file)
- **Pin versions** for production services to avoid unexpected changes

### Environment-Specific Configuration
- Development: `.env.local` (gitignored)
- CI: GitHub Secrets injected as env vars
- Production: Platform-specific env var management (Render, Railway, Cloud Run)

**Sources:**
- [FastAPI Settings Management](https://fastapi.tiangolo.com/advanced/settings/)
- [GitHub Secrets Management](https://dev.to/kafeel_ahmad/mastering-github-actions-environment-variables-and-secrets-management-5gho)
- [FastAPI Secrets Best Practices](https://python.plainenglish.io/managing-configuration-and-secrets-in-fastapi-and-python-apps-best-practices-for-security-and-7027076f8179)

---

## 3. Backend Security Hardening

### CORS Configuration
**Production settings** (avoid `allow_origins=["*"]`):
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Explicit origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "Accept", "Origin"],
)
```

### Rate Limiting
- Use **slowapi** (Redis backend for multi-instance apps)
- Per-IP for anonymous, per-user for authenticated
- Example: `@limiter.limit("100/minute")` or `@limiter.limit("5/minute")`
- Recommended: 100 requests per 60 seconds for general endpoints

### Security Headers
Add middleware for:
- `Strict-Transport-Security` (HSTS)
- `Content-Security-Policy` (CSP)
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`

Execute security middleware **before** business logic middleware.

### Input Validation
- Pydantic models validate all request bodies automatically
- Sanitize path/query parameters
- Implement authentication/authorization checks

**Sources:**
- [FastAPI Production Best Practices](https://render.com/articles/fastapi-production-deployment-best-practices)
- [Production-Ready FastAPI](https://oneuptime.com/blog/post/2026-01-27-fastapi-production/view)
- [FastAPI Security Guide](https://davidmuraya.com/blog/fastapi-security-guide/)
- [CORS Configuration](https://fastapi.tiangolo.com/tutorial/cors/)

---

## 4. Database Connection Security (Supabase)

### Connection Pooling
- **All new Supabase projects include PgBouncer** (port 6543)
- **Supavisor** is replacing PgBouncer (new pooler)
- Connection strings:
  - Direct: `postgres://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres`
  - Pooled (PgBouncer): `postgres://postgres:[PASSWORD]@db.xxx.supabase.co:6543/postgres`
  - Pooled (Supavisor): `postgres://postgres.xxx:[PASSWORD]@aws-0-region.pooler.supabase.com:6543/postgres`

### PgBouncer Settings
- Runs in **Transaction mode** (does not support prepared statements)
- Pool size configurable in Supabase dashboard
- Use pooled connection for FastAPI backend (handles concurrent connections)

### SSL Enforcement
- **Enable SSL enforcement** in Supabase dashboard to prevent non-SSL connections
- Connection strings automatically use SSL
- Increased security for production

### Row Level Security (RLS)
- Enable RLS on all tables
- supabase-js client handles authorization automatically
- Write policies for insert, select, update, delete operations
- Use `auth.uid()` in policies for user-based access control

**Sources:**
- [Supabase Connection Pooling](https://www.restack.io/docs/supabase-knowledge-supabase-connection-pooling)
- [PgBouncer in Supabase](https://supabase.com/blog/supabase-pgbouncer)
- [SSL Enforcement](https://supabase.com/docs/guides/platform/ssl-enforcement)
- [Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)

---

## 5. Monitoring & Logging

### Free/Cheap Options for Small Apps

#### Sentry (Error Tracking)
- **Best for**: Developer-centric error monitoring, performance tracing
- **Free tier**: Generous for small apps
- **Features**: Stack traces, breadcrumbs, release tracking, performance monitoring
- **Pricing**: Free tier available, paid starts at reasonable rate

#### Better Stack
- **Best for**: All-in-one observability (logs, traces, metrics, incidents)
- **Pricing**: Sentry-compatible at ~1/6th price, includes more features
- **Free tier**: 5 monitors (tight), paid $24/mo (steep jump)
- **UI**: Best-looking interface in category

#### UptimeRobot (Uptime Monitoring)
- **Best for**: Simple "Is it up?" checks
- **Free tier**: 50 monitors, 5-minute check intervals
- **Features**: HTTP/HTTPS, ping, port monitoring, status pages
- **Recommendation**: Perfect starting point for solo devs/small projects
- **Pricing**: Free tier is generous, no cost to start

### Recommendations for Small Apps
- **Start with**: UptimeRobot (free uptime checks) + Sentry (free error tracking)
- **Scale to**: Better Stack when needing centralized logs/metrics
- **Solo devs**: UptimeRobot + Uptime Kuma (self-hosted alternative)

**Sources:**
- [Datadog vs Sentry 2026](https://betterstack.com/community/comparisons/datadog-vs-sentry/)
- [Best Free Uptime Monitoring 2026](https://perkydash.com/comparison/best-free-uptime-monitoring)
- [UptimeRobot Comparison](https://uptimerobot.com/knowledge-hub/monitoring/11-best-uptime-monitoring-tools-compared/)

---

## Key Takeaways

1. **CI/CD**: Use path-filtered monorepo workflows, separate CI/CD, aggressive caching
2. **Secrets**: GitHub Secrets + Pydantic BaseSettings, never commit `.env`
3. **Security**: Explicit CORS origins, rate limiting (slowapi), security headers middleware
4. **Database**: Use Supabase pooled connection (port 6543), enable SSL enforcement, implement RLS
5. **Monitoring**: Start free with UptimeRobot + Sentry, scale to Better Stack if needed

## Unresolved Questions
- Which deployment platform chosen? (Render, Railway, Cloud Run, Vercel/Railway combo) - affects env var injection method
- Current Supabase connection string format? (PgBouncer vs Supavisor) - check dashboard
- Expected traffic volume? - determines rate limit thresholds
