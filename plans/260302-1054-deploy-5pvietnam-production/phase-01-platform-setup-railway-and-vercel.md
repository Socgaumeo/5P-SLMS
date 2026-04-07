# Phase 1: Platform Setup (Railway + Vercel)

## Context Links
- [Research: Hosting Platforms](research/researcher-01-hosting-platforms.md)
- [Backend Dockerfile](../../backend/Dockerfile)
- [Frontend vercel.json](../../frontend/vercel.json)
- [Deploy Backend Workflow](../../.github/workflows/deploy-backend-to-railway.yml)
- [Deploy Frontend Workflow](../../.github/workflows/deploy-frontend-to-vercel.yml)

## Overview
- **Priority**: P1 (blocking all other phases)
- **Status**: pending
- **Effort**: 45 min
- **Description**: Create Railway + Vercel projects, connect GitHub repo, configure env vars, verify first deploys work

## Key Insights
- CI/CD workflows already exist for both platforms
- Backend Dockerfile uses python:3.12-slim + gunicorn+uvicorn on port 8000
- Frontend has `vercel.json` with SPA rewrites
- Railway uses nixpacks-action; Vercel uses vercel-action
- Backend requires env vars validated by Pydantic at startup (DATABASE_URL, SECRET_KEY, JWT_SECRET_KEY when DEBUG=False)

## Requirements

### Functional
- Railway project created, linked to `backend/` directory
- Vercel project created, linked to `frontend/` directory
- First deploy succeeds for both platforms
- Health endpoint (`/health` or `/`) responds on Railway

### Non-Functional
- Deploy time < 5 min per platform
- No secrets exposed in logs

## Architecture

```
GitHub repo (main branch)
  ├── backend/** change → GitHub Actions → Railway deploy (nixpacks/Docker)
  └── frontend/** change → GitHub Actions → Vercel deploy (vercel-action)
```

## Related Code Files
- `backend/Dockerfile` - Docker build for Railway
- `backend/gunicorn_conf.py` - 1 worker, port 8000
- `backend/app/core/config.py` - Pydantic Settings with validation
- `frontend/vercel.json` - SPA rewrite rules
- `frontend/package.json` - build script: `vite build`
- `.github/workflows/deploy-backend-to-railway.yml`
- `.github/workflows/deploy-frontend-to-vercel.yml`

## Implementation Steps

### Railway Backend Setup
1. Go to [railway.app](https://railway.app), sign in with GitHub
2. Create new project > "Deploy from GitHub repo"
3. Select `5P-SLMS` repo
4. Set **Root Directory** to `backend`
5. Railway auto-detects Dockerfile; confirm it uses `backend/Dockerfile`
6. Add environment variables (Settings > Variables):
   ```
   DATABASE_URL=<supabase pooled connection string, port 6543>
   SUPABASE_URL=<your supabase project url>
   SUPABASE_SERVICE_ROLE_KEY=<service role key>
   SUPABASE_ANON_KEY=<anon key>
   AI_PROVIDER=anthropic
   ANTHROPIC_API_KEY=<key>
   GOOGLE_GEMINI_API_KEY=<key>
   DEEPSEEK_API_KEY=<key>
   SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
   JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480
   DEBUG=False
   ALLOWED_ORIGINS=https://5pvietnam.com,https://www.5pvietnam.com
   PORT=8000
   ```
7. Deploy manually once; check build logs
8. Verify: `curl https://<railway-url>/` returns JSON with version info
9. Copy the Railway deploy token; save as `RAILWAY_TOKEN` GitHub Secret

### Vercel Frontend Setup
1. Go to [vercel.com](https://vercel.com), sign in with GitHub
2. Import `5P-SLMS` repo
3. Set **Root Directory** to `frontend`
4. Framework preset: Vite
5. Build command: `npm run build` (auto-detected)
6. Output directory: `dist` (Vite default)
7. Add environment variable:
   ```
   VITE_API_URL=https://api.5pvietnam.com
   ```
8. Deploy; verify build succeeds
9. Copy Vercel project tokens:
   - `VERCEL_TOKEN` (Account Settings > Tokens)
   - `VERCEL_ORG_ID` (from `.vercel/project.json` or Project Settings)
   - `VERCEL_PROJECT_ID` (from Project Settings > General)
10. Save all three as GitHub Secrets

### GitHub Secrets Setup
1. Go to repo Settings > Secrets and variables > Actions
2. Add these repository secrets:
   - `RAILWAY_TOKEN`
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`

## Todo List
- [ ] Create Railway project + connect repo
- [ ] Set Railway root directory to `backend`
- [ ] Add all env vars to Railway
- [ ] Verify Railway first deploy succeeds
- [ ] Create Vercel project + connect repo
- [ ] Set Vercel root directory to `frontend`
- [ ] Add `VITE_API_URL` env var to Vercel
- [ ] Verify Vercel first deploy succeeds
- [ ] Add RAILWAY_TOKEN to GitHub Secrets
- [ ] Add VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID to GitHub Secrets

## Success Criteria
- `curl https://<railway-url>/` returns `{"message": "SLMS Backend API", "version": "1.0.0", "docs": "/docs"}`
- Frontend loads on Vercel URL without errors
- GitHub Actions deploy workflow runs successfully on next push

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Railway build fails due to system deps | Low | Medium | Dockerfile already installs libpq-dev + gcc |
| Pydantic validation fails at startup | Medium | High | Set ALL required env vars before deploy; check logs |
| Vercel build OOM | Low | Low | Free tier has 1024MB; React app is small |

## Security Considerations
- Generate cryptographically strong SECRET_KEY and JWT_SECRET_KEY (min 32 bytes)
- Never log env var values; Railway/Vercel redact by default
- Use Supabase **pooled** connection string (port 6543) for production
- Verify `.env` is in `.gitignore`

## Next Steps
- After both deploys work: proceed to Phase 2 (Domain & DNS)
- Backend URL will be temporary Railway URL until custom domain configured
- Frontend `VITE_API_URL` points to `api.5pvietnam.com`; API calls will fail until DNS is set up (Phase 2)
