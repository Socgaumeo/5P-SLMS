# Phase 03: Deploy Backend to Railway

## Context Links

- [plan.md](plan.md) - Overview
- [phase-01](phase-01-prepare-production-configs.md) - Dockerfile, gunicorn, config changes
- [backend/main.py](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/main.py) - FastAPI app
- [backend/requirements.txt](/Users/bear1108/Documents/GitHub/5P-SLMS/backend/requirements.txt) - Dependencies

## Overview

- **Priority**: P1
- **Status**: pending
- **Effort**: 45m
- **Description**: Deploy FastAPI backend to Railway with Dockerfile, env vars, and custom subdomain api.5pvietnam.com

## Key Insights

- Railway detects Dockerfile automatically; no nixpacks config needed
- Railway Singapore region available - minimizes latency to Supabase (same region)
- Railway Hobby plan: $5/mo, 8GB RAM, 8 vCPU (sufficient for internal tool)
- `PORT` env var is auto-injected by Railway; gunicorn_conf.py already reads it
- Database is external (Supabase) - no Railway DB needed
- Health endpoint exists at `/health` - use for Railway health checks

## Requirements

### Functional
- API accessible at `https://api.5pvietnam.com`
- All existing endpoints work (chat, jobs, auth, search, exports, health)
- Database connection to Supabase Singapore works with low latency
- AI API calls (Anthropic, Gemini, DeepSeek) work from Railway

### Non-Functional
- Response time < 500ms for DB queries
- Auto-restart on crash
- Zero-downtime deploys (Railway rolling deploys)
- Memory < 512MB typical usage

## Architecture

```
Railway Service (Singapore region)
├── Docker container
│   ├── python:3.12-slim
│   ├── gunicorn + uvicorn workers
│   └── FastAPI app
├── Env vars (DATABASE_URL, API keys, JWT secrets)
├── Custom domain: api.5pvietnam.com
└── Health check: /health

Connections:
  Railway --> Supabase PG (ap-southeast-1, same region)
  Railway --> Anthropic API (external)
  Railway --> DeepSeek API (external)
  Railway --> Gemini API (external)
```

## Related Code Files

### Files Required (from Phase 01)
- `backend/Dockerfile`
- `backend/gunicorn_conf.py`
- `backend/.dockerignore`
- `backend/app/core/config.py` (updated with ALLOWED_ORIGINS)
- `backend/main.py` (updated CORS)

## Implementation Steps

### 1. Create Railway Account & Project

1. Go to [railway.app](https://railway.app), sign up with GitHub
2. Click "New Project" > "Deploy from GitHub repo"
3. Select `Socgaumeo/5P-SLMS` repository
4. **CRITICAL**: Set Root Directory to `backend` in Service Settings

### 2. Configure Service Settings

In Railway service settings:

| Setting | Value |
|---------|-------|
| Root Directory | `backend` |
| Builder | Dockerfile |
| Region | `ap-southeast-1` (Singapore) |
| Restart Policy | Always |
| Health Check Path | `/health` |
| Health Check Timeout | 10s |

### 3. Set Environment Variables

In Railway service > Variables tab, add ALL of these:

```
# Database
DATABASE_URL=postgresql://postgres.ooixntyflwmjaryxwakx:PASSWORD@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres
SUPABASE_URL=https://ooixntyflwmjaryxwakx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<from Supabase dashboard>
SUPABASE_ANON_KEY=<from Supabase dashboard>

# AI
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=<key>
GOOGLE_GEMINI_API_KEY=<key>
ANTHROPIC_API_KEY=<key>

# Application
DEBUG=false
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(64))">
JWT_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(64))">
ALLOWED_ORIGINS=https://5pvietnam.com,https://www.5pvietnam.com

# Railway auto-sets PORT; gunicorn_conf.py reads it
```

**Generate secrets locally**:
```bash
python3 -c "import secrets; print('SECRET_KEY:', secrets.token_urlsafe(64))"
python3 -c "import secrets; print('JWT_SECRET_KEY:', secrets.token_urlsafe(64))"
```

### 4. Deploy & Test Initial Build

1. Railway auto-deploys on push to main
2. Check build logs for errors
3. Test health endpoint at Railway-provided URL: `https://<service>.up.railway.app/health`
4. Test DB health: `https://<service>.up.railway.app/health/db`
5. Test API docs: `https://<service>.up.railway.app/docs`

### 5. Add Custom Domain

1. Railway Dashboard > Service > Settings > Domains
2. Click "Custom Domain"
3. Enter `api.5pvietnam.com`
4. Railway provides CNAME target (e.g., `<service>.up.railway.app`)
5. Configure DNS in Phase 04

### 6. Verify All Endpoints

Test these endpoints against the Railway URL:

```bash
# Health
curl https://api.5pvietnam.com/health

# DB connectivity
curl https://api.5pvietnam.com/health/db

# Auth - login
curl -X POST https://api.5pvietnam.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# API docs
curl https://api.5pvietnam.com/docs
```

## Todo List

- [ ] Create Railway account with GitHub OAuth
- [ ] Import repo and set Root Directory to `backend`
- [ ] Select Singapore region
- [ ] Set builder to Dockerfile
- [ ] Set ALL environment variables (12+ vars)
- [ ] Generate and set SECRET_KEY and JWT_SECRET_KEY
- [ ] Trigger first deploy and monitor build logs
- [ ] Test `/health` and `/health/db` endpoints
- [ ] Add custom domain `api.5pvietnam.com`
- [ ] Configure health check path to `/health`
- [ ] Full API test after DNS setup (Phase 04)

## Success Criteria

- Railway build succeeds (Docker image builds)
- `/health` returns `{"status": "healthy"}`
- `/health/db` returns `{"status": "healthy", "database": "connected"}`
- API docs load at `/docs`
- CORS headers present on responses (allow 5pvietnam.com)
- No hardcoded secrets in logs or responses

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Docker build fails on Railway | Low | High | Test locally first: `docker build -t test .` |
| Database connection timeout | Low | Medium | Both in Singapore; verify connection pooler URL |
| Memory exceeded on Hobby plan | Low | Medium | 2 gunicorn workers sufficient; monitor usage |
| AI API keys rate-limited | Low | Low | Already working locally; same keys |
| Railway Singapore unavailable | Very Low | High | Fallback: US-West region (higher latency) |

## Security Considerations

- **Env vars**: Stored encrypted in Railway; never in logs
- **Network**: Railway provides automatic HTTPS
- **DB access**: Connection via Supabase pooler with password (already URL-encoded)
- **API keys**: All AI keys stored as Railway env vars, not in code
- **Health endpoint**: `/health/db` reveals minimal info; no credentials exposed

## Next Steps

- Phase 04: Configure DNS to point `api.5pvietnam.com` to Railway CNAME target
- Phase 05: Automate deploys via GitHub Actions (optional - Railway auto-deploys from GitHub)
