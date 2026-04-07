---
title: "Deploy 5P-SLMS to 5pvietnam.com"
description: "Production deployment of FastAPI backend + React frontend to Railway + Vercel with custom domain"
status: pending
priority: P1
effort: 4h
branch: main
tags: [deployment, production, railway, vercel, dns, security]
created: 2026-03-02
---

# Deploy 5P-SLMS to Production (5pvietnam.com)

## Stack Decision

**Option A (Recommended)**: Railway (backend) + Vercel (frontend)
- CI/CD already configured in `.github/workflows/`
- Minimal new setup required; just platform config, DNS, env vars, hardening
- Cost: ~$5-10/mo (Railway) + $0 (Vercel free tier)

**Option B (Asia-Optimized)**: Fly.io (backend) + Cloudflare Pages (frontend)
- Better latency from Singapore (~20-50ms vs 200-300ms)
- Requires rewriting CI/CD workflows
- Cost: ~$5-10/mo total

Recommend **Option A** for fastest path to production. Migrate to Option B later if latency is an issue.

## Phases

| # | Phase | Effort | Status | File |
|---|-------|--------|--------|------|
| 1 | Platform Setup (Railway + Vercel) | 45min | pending | [phase-01](phase-01-platform-setup-railway-and-vercel.md) |
| 2 | Domain & DNS Configuration | 30min | pending | [phase-02](phase-02-domain-and-dns-configuration.md) |
| 3 | Backend Production Hardening | 1.5h | pending | [phase-03](phase-03-backend-production-hardening.md) |
| 4 | Frontend Production Build | 30min | pending | [phase-04](phase-04-frontend-production-build-and-config.md) |
| 5 | CI/CD & Monitoring | 45min | pending | [phase-05](phase-05-cicd-pipeline-and-monitoring-setup.md) |

## Key Dependencies

- Domain registrar access for 5pvietnam.com DNS records
- Railway account + RAILWAY_TOKEN
- Vercel account + VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID
- All env vars from `.env` (DATABASE_URL, Supabase keys, AI keys, JWT secrets)
- Supabase project already running in Singapore ap-southeast-1

## Architecture

```
[5pvietnam.com] --> Vercel CDN --> React SPA
[api.5pvietnam.com] --> Railway --> FastAPI (gunicorn+uvicorn)
                                      |
                              Supabase PostgreSQL (Singapore)
```

## Risk Summary

- Railway may have higher latency from Asia (~200-300ms); acceptable for internal tool
- Single gunicorn worker (in-memory conversation state); fine for <100 concurrent users
- Supabase free tier connection limits; monitor pooler usage
