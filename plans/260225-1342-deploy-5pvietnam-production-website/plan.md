---
title: "Deploy 5P-SLMS to 5pvietnam.com"
description: "Deploy FastAPI+React app to production using Vercel+Railway with CI/CD"
status: validated
priority: P1
effort: 4h
branch: main
tags: [deployment, production, vercel, railway, ci-cd]
created: 2026-02-25
---

# Deploy 5P-SLMS to 5pvietnam.com

## Validation Summary

- **Domain registrar**: Google Domains (now Squarespace Domains)
- **Hosting**: Vercel (frontend free) + Railway (backend $5/mo) - simplest setup
- **CI/CD**: GitHub Actions auto-deploy on push
- **Budget**: $20-100/mo acceptable, prioritize performance & stability
- **Accounts needed**: Create Vercel + Railway (only GitHub exists)
- **Repo**: Public (for AI agent access) - CRITICAL: remove hardcoded credentials from config.py
- **Users**: Internal team (5-20 people)

## Architecture

```
User --> 5pvietnam.com (Vercel/CDN) --> React SPA
         api.5pvietnam.com (Railway/Singapore) --> FastAPI --> Supabase PG (Singapore)
```

## CRITICAL SECURITY: Remove hardcoded DB credentials from config.py (line 14) before deployment!

## Phases

| # | Phase | Effort | Status | Deps |
|---|-------|--------|--------|------|
| 0 | [Security: Remove hardcoded secrets](phase-00-remove-hardcoded-secrets.md) | 15m | pending | - |
| 1 | [Prepare Production Configs](phase-01-prepare-production-configs.md) | 1h | pending | Phase 0 |
| 2 | [Deploy Frontend (Vercel)](phase-02-deploy-frontend-to-vercel.md) | 30m | pending | Phase 1 |
| 3 | [Deploy Backend (Railway)](phase-03-deploy-backend-to-railway.md) | 45m | pending | Phase 1 |
| 4 | [DNS + SSL + Domain Setup](phase-04-dns-ssl-domain-setup.md) | 30m | pending | Phase 2+3 |
| 5 | [Setup CI/CD (GitHub Actions)](phase-05-setup-cicd-github-actions.md) | 45m | pending | Phase 4 |
| 6 | [Production Hardening & Monitoring](phase-06-production-hardening-and-monitoring.md) | 30m | pending | Phase 4 |

**Execution**: Phase 0 → 1 → 2+3 (parallel) → 4 → 5+6 (parallel)

## Key Dependencies

- Domain: 5pvietnam.com (Google Domains / Squarespace)
- Database: Supabase PostgreSQL ap-southeast-1 (already running)
- AI APIs: Anthropic, Gemini, DeepSeek keys (in .env)
- GitHub repo: Socgaumeo/5P-SLMS (public)

## Critical Config Changes

1. `backend/app/core/config.py` - REMOVE hardcoded DATABASE_URL, DEBUG=False, env-based CORS, strong secrets
2. `backend/main.py` - CORS restrict to `https://5pvietnam.com`
3. New files: `Dockerfile`, `gunicorn_conf.py`, `.env.example`, GitHub Actions workflows

## Cost Estimate

| Service | Plan | Cost/mo |
|---------|------|---------|
| Vercel | Free (Hobby) | $0 |
| Railway | Developer ($5) or Team ($20) | $5-20 |
| Supabase | Free/Pro | $0-25 |
| Domain DNS | Google Domains / Cloudflare | $0 |
| **Total** | | **$5-45** |

## Success Criteria

- [ ] No hardcoded credentials in codebase
- [ ] https://5pvietnam.com loads React app
- [ ] https://api.5pvietnam.com/health returns healthy
- [ ] Login, chat, job CRUD all work end-to-end
- [ ] Auto-deploy on git push to main
- [ ] HTTPS enforced, CORS locked down
