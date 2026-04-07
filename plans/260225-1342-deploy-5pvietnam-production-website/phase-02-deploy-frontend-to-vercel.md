# Phase 02: Deploy Frontend to Vercel

## Context Links

- [plan.md](plan.md) - Overview
- [phase-01](phase-01-prepare-production-configs.md) - Prerequisite
- [frontend/package.json](/Users/bear1108/Documents/GitHub/5P-SLMS/frontend/package.json) - Build scripts
- [frontend/vite.config.js](/Users/bear1108/Documents/GitHub/5P-SLMS/frontend/vite.config.js) - Vite config

## Overview

- **Priority**: P1
- **Status**: pending
- **Effort**: 30m
- **Description**: Deploy React/Vite frontend to Vercel free tier with custom domain 5pvietnam.com

## Key Insights

- Frontend is a standard Vite+React SPA, Vercel auto-detects framework
- `VITE_API_URL` is already used in codebase via `import.meta.env.VITE_API_URL || 'http://localhost:8000'`
- Vercel auto-provisions SSL for custom domains
- Frontend code is in `frontend/` subdirectory (not root) - must set Root Directory in Vercel
- No SSR, no API routes in frontend - pure SPA deployment
- Vite 7 + React 19 - modern stack, fully compatible with Vercel

## Requirements

### Functional
- SPA served from `https://5pvietnam.com`
- All API calls go to `https://api.5pvietnam.com`
- Client-side routing works (all paths serve index.html)
- Fast load times for Vietnam users (Vercel edge CDN)

### Non-Functional
- Build time < 60s
- First paint < 2s (Vercel edge)
- Zero-downtime deploys

## Architecture

```
GitHub push (frontend/**) --> Vercel auto-build
                              ├── npm install
                              ├── npm run build (vite build)
                              └── serve dist/ as static SPA

5pvietnam.com --> Vercel Edge CDN --> dist/index.html (SPA)
                                     dist/assets/* (JS/CSS)
```

## Related Code Files

### Files to Create
- `frontend/vercel.json` (optional - SPA rewrites config)

### Files Unchanged
- `frontend/vite.config.js` - No changes needed
- `frontend/package.json` - No changes needed

## Implementation Steps

### 1. Create Vercel Account & Import Project

1. Go to [vercel.com](https://vercel.com), sign up with GitHub
2. Click "Add New Project"
3. Import `Socgaumeo/5P-SLMS` repository
4. **CRITICAL**: Set Root Directory to `frontend`

### 2. Configure Build Settings

In Vercel project settings:

| Setting | Value |
|---------|-------|
| Framework Preset | Vite |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Install Command | `npm install` |
| Node.js Version | 20.x |

### 3. Set Environment Variables

In Vercel dashboard > Settings > Environment Variables:

| Variable | Value | Environment |
|----------|-------|-------------|
| `VITE_API_URL` | `https://api.5pvietnam.com` | Production |
| `VITE_API_URL` | `http://localhost:8000` | Development |

**Note**: `VITE_` prefix is required for Vite to expose vars to client code.

### 4. Create `frontend/vercel.json` (SPA routing)

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

This ensures client-side routing works (all paths serve index.html).

### 5. Add Custom Domain

1. Vercel Dashboard > Project > Settings > Domains
2. Add `5pvietnam.com`
3. Add `www.5pvietnam.com` (auto-redirect to apex)
4. Vercel provides DNS records to configure (see Phase 04)

### 6. Deploy & Verify

1. Push to main branch triggers auto-deploy
2. Verify at `https://your-project.vercel.app` first (Vercel preview URL)
3. After DNS setup (Phase 04), verify at `https://5pvietnam.com`

### 7. Test Checklist

- [ ] Homepage loads
- [ ] Login form appears
- [ ] Network tab shows API calls to `https://api.5pvietnam.com`
- [ ] Browser console has no CORS errors (after Phase 03 backend is up)
- [ ] Refreshing on sub-routes returns the SPA (not 404)

## Todo List

- [ ] Create Vercel account and import GitHub repo
- [ ] Set Root Directory to `frontend`
- [ ] Configure build settings (Vite preset)
- [ ] Set `VITE_API_URL` env var
- [ ] Create `frontend/vercel.json` for SPA rewrites
- [ ] Add custom domain `5pvietnam.com`
- [ ] Trigger first deploy and verify preview URL
- [ ] Full E2E test after backend + DNS are ready

## Success Criteria

- Vercel build succeeds (green checkmark)
- Preview URL loads the React app
- `VITE_API_URL` correctly baked into built JS bundle
- SPA routing works on all paths (no 404s on refresh)

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Build fails on Vercel | Low | Medium | Test `npm run build` locally first |
| Root dir misconfigured | Medium | High | Double-check it's set to `frontend` not root |
| VITE_API_URL not baked in | Low | High | Verify in built JS; must be set BEFORE build |
| Vercel free tier limits | Low | Low | 100GB bandwidth/mo is plenty for internal tool |

## Security Considerations

- No secrets in frontend code (only `VITE_API_URL` which is public)
- HTTPS enforced by Vercel by default
- Headers: Vercel adds security headers; can customize in `vercel.json`

## Next Steps

- Phase 03: Deploy backend to Railway (so API calls work)
- Phase 04: DNS setup to point 5pvietnam.com to Vercel
