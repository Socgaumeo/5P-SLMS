# Phase 01: Prepare Production Configs

## Context Links

- [plan.md](plan.md) - Overview
- [backend/app/core/config.py](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/core/config.py) - Settings class
- [backend/main.py](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/main.py) - CORS config, app entry
- [frontend/vite.config.js](/Users/bear1108/Documents/GitHub/5P-SLMS/frontend/vite.config.js) - Vite build config

## Overview

- **Priority**: P1 (blocking all other phases)
- **Status**: pending
- **Effort**: 1h
- **Description**: Create production-ready configs: Dockerfile, gunicorn, env-based CORS, secure defaults

## Key Insights

- `config.py` has hardcoded `SECRET_KEY` and `JWT_SECRET_KEY` defaults - must be overridden via env vars in production
- `main.py` CORS is `allow_origins=["*"]` - must restrict to `https://5pvietnam.com`
- Frontend already uses `import.meta.env.VITE_API_URL || 'http://localhost:8000'` pattern - just set `VITE_API_URL` at build time
- No Dockerfile exists; Railway needs one for Python deployment
- `.gitignore` is minimal (only `.env` and `.DS_Store`) - needs expansion

## Requirements

### Functional
- Backend runs via gunicorn+uvicorn workers in production
- CORS only allows `https://5pvietnam.com` and `https://www.5pvietnam.com`
- All secrets sourced from environment variables (never hardcoded defaults)
- Frontend builds with correct `VITE_API_URL` pointing to `https://api.5pvietnam.com`

### Non-Functional
- Docker image < 500MB
- Cold start < 10s
- No credentials in Docker image or git history

## Architecture

```
Dockerfile (backend/)
├── python:3.12-slim base
├── pip install requirements.txt
├── gunicorn_conf.py (workers, bind, timeouts)
└── CMD: gunicorn backend.main:app -c gunicorn_conf.py
```

## Related Code Files

### Files to Modify
- `backend/app/core/config.py` - Add `ALLOWED_ORIGINS`, change `DEBUG` default to `False`
- `backend/main.py` - Use `settings.ALLOWED_ORIGINS` for CORS

### Files to Create
- `backend/Dockerfile`
- `backend/gunicorn_conf.py`
- `backend/.dockerignore`
- `.env.example` (root-level template)

### Files to Update
- `.gitignore` - Add `__pycache__/`, `*.pyc`, `node_modules/`, `dist/`, etc.

## Implementation Steps

### 1. Update `backend/app/core/config.py`

Add these fields to `Settings` class:

```python
# Application
DEBUG: bool = False  # Changed from True
SECRET_KEY: str = "MUST-SET-IN-PRODUCTION"
ALLOWED_ORIGINS: str = "https://5pvietnam.com,https://www.5pvietnam.com"

# JWT Authentication
JWT_SECRET_KEY: str = "MUST-SET-IN-PRODUCTION"
```

Add a validator that raises error if defaults are used when DEBUG=False:

```python
@model_validator(mode='after')
def validate_production_secrets(self):
    if not self.DEBUG:
        if "MUST-SET" in self.SECRET_KEY or "MUST-SET" in self.JWT_SECRET_KEY:
            raise ValueError("SECRET_KEY and JWT_SECRET_KEY must be set in production")
    return self
```

### 2. Update `backend/main.py` CORS

Replace the hardcoded `allow_origins=["*"]` with:

```python
# CORS - parse comma-separated origins from settings
allowed_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")]
if settings.DEBUG:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. Create `backend/Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn uvloop httptools

COPY . .

EXPOSE 8000

CMD ["gunicorn", "main:app", "-c", "gunicorn_conf.py"]
```

### 4. Create `backend/gunicorn_conf.py`

```python
import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(os.getenv("WEB_CONCURRENCY", min(multiprocessing.cpu_count() * 2 + 1, 4)))
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = "info"
```

### 5. Create `backend/.dockerignore`

```
__pycache__/
*.pyc
.env
.git/
.gitignore
*.md
tests/
scripts/
```

### 6. Create root `.env.example`

```env
# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://user:pass@host:6543/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_ANON_KEY=

# AI
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=
GOOGLE_GEMINI_API_KEY=
ANTHROPIC_API_KEY=

# Application
DEBUG=false
SECRET_KEY=generate-a-64-char-random-string
JWT_SECRET_KEY=generate-another-64-char-random-string
ALLOWED_ORIGINS=https://5pvietnam.com,https://www.5pvietnam.com

# Frontend (set in Vercel)
VITE_API_URL=https://api.5pvietnam.com
```

### 7. Update `.gitignore`

Append:

```
__pycache__/
*.pyc
*.pyo
node_modules/
dist/
.env*
!.env.example
.DS_Store
*.log
```

## Todo List

- [ ] Update `config.py` with `ALLOWED_ORIGINS`, `DEBUG=False` default, production secret validators
- [ ] Update `main.py` CORS to use `settings.ALLOWED_ORIGINS`
- [ ] Create `backend/Dockerfile`
- [ ] Create `backend/gunicorn_conf.py`
- [ ] Create `backend/.dockerignore`
- [ ] Create root `.env.example`
- [ ] Update `.gitignore` with comprehensive ignores
- [ ] Test Docker build locally: `cd backend && docker build -t slms-backend .`
- [ ] Test Docker run locally: `docker run -p 8000:8000 --env-file ../.env slms-backend`

## Success Criteria

- `docker build` succeeds with no errors
- `docker run` starts gunicorn with uvicorn workers
- `/health` endpoint responds with `{"status": "healthy"}`
- CORS rejects requests from non-allowed origins
- App refuses to start if SECRET_KEY not overridden when DEBUG=False

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| psycopg2 compile fails in Docker | Low | High | Using `python:3.12-slim` + `gcc libpq-dev` |
| .env not loaded in Docker | Medium | High | pydantic-settings reads env vars directly (no .env needed) |
| Existing hardcoded DB URL leaks | Medium | High | Override via env var; never commit .env |

## Security Considerations

- **Secrets**: All sensitive values via env vars, never in code or Docker image
- **CORS**: Locked to specific origins in production
- **Debug**: Disabled by default (no stack traces to users)
- **Docker**: Non-root user recommended (add `USER nobody` if Railway supports it)

## Next Steps

- Phase 02 depends on this phase (frontend needs `VITE_API_URL` env var pattern confirmed)
- Phase 03 depends on Dockerfile being ready
