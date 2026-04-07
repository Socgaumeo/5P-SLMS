# Phase 5: CI/CD Pipeline & Monitoring Setup

## Context Links
- [Research: CI/CD & Security](research/researcher-02-cicd-security.md)
- [Deploy Backend Workflow](../../.github/workflows/deploy-backend-to-railway.yml)
- [Deploy Frontend Workflow](../../.github/workflows/deploy-frontend-to-vercel.yml)

## Overview
- **Priority**: P2
- **Status**: pending
- **Effort**: 45 min
- **Description**: Verify/update existing CI/CD workflows, add basic monitoring with UptimeRobot, optionally add Sentry error tracking

## Key Insights
- CI/CD already exists: Railway deploys on `backend/**` push, Vercel on `frontend/**` push
- Current workflows are minimal (no tests, no linting, no caching)
- No monitoring or alerting currently configured
- UptimeRobot free tier: 50 monitors, 5-min intervals (perfect for this scale)
- Sentry has generous free tier for error tracking

## Requirements

### Functional
- Push to `main` auto-deploys affected service (backend/frontend)
- Deployment failures trigger notification (GitHub Actions email by default)
- Uptime monitoring checks API health every 5 minutes
- Error tracking captures unhandled exceptions in production

### Non-Functional
- CI/CD pipeline completes in < 5 minutes
- Monitoring alerts within 5 minutes of downtime

## Architecture

```
Push to main
  ├── backend/** → deploy-backend-to-railway.yml → Railway
  └── frontend/** → deploy-frontend-to-vercel.yml → Vercel

Monitoring:
  UptimeRobot → GET https://api.5pvietnam.com/ (every 5 min)
  UptimeRobot → GET https://5pvietnam.com (every 5 min)

Error Tracking (optional):
  Backend → Sentry Python SDK → sentry.io
  Frontend → Sentry React SDK → sentry.io
```

## Related Code Files

### Files to Modify (optional improvements)
- `.github/workflows/deploy-backend-to-railway.yml` - Add caching, concurrency control
- `.github/workflows/deploy-frontend-to-vercel.yml` - Add caching, concurrency control

### Files to Potentially Create (optional)
- `backend/app/core/sentry-config.py` - Sentry initialization (if adding error tracking)

## Implementation Steps

### 1. Verify Existing Workflows Work

Existing backend workflow (`deploy-backend-to-railway.yml`):
```yaml
name: Deploy Backend to Railway
on:
  push:
    branches: [main]
    paths: ['backend/**']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: railwayapp/nixpacks-action@v1
        with:
          railway-token: ${{ secrets.RAILWAY_TOKEN }}
```

Existing frontend workflow (`deploy-frontend-to-vercel.yml`):
```yaml
name: Deploy Frontend to Vercel
on:
  push:
    branches: [main]
    paths: ['frontend/**']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
        working-directory: frontend
      - run: npm run build
        working-directory: frontend
      - uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: frontend
          vercel-args: '--prod'
```

**Verification**: Push a small change to each directory, check Actions tab for green status.

### 2. Add Concurrency Control (Recommended)

Add to both workflows to cancel stale deploys:
```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

### 3. Add Build Caching (Optional)

For frontend workflow, add npm cache:
```yaml
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'
    cache-dependency-path: frontend/package-lock.json
```

### 4. Set Up UptimeRobot Monitoring

1. Go to [uptimerobot.com](https://uptimerobot.com), create free account
2. Add Monitor #1:
   - Type: HTTPS
   - URL: `https://api.5pvietnam.com/`
   - Interval: 5 minutes
   - Alert contact: your email
3. Add Monitor #2:
   - Type: HTTPS
   - URL: `https://5pvietnam.com`
   - Interval: 5 minutes
   - Alert contact: your email
4. (Optional) Create a public status page at `status.5pvietnam.com`

### 5. Add Sentry Error Tracking (Optional - Phase 5b)

**Backend** (if desired):
```bash
pip install sentry-sdk[fastapi]
```

Add to `backend/main.py`:
```python
import sentry_sdk

if not settings.DEBUG:
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN", ""),
        traces_sample_rate=0.1,
    )
```

Add `SENTRY_DSN` env var to Railway.

**Frontend** (if desired):
```bash
npm install @sentry/react
```

Add to `frontend/src/main.jsx`:
```javascript
import * as Sentry from "@sentry/react";

if (import.meta.env.PROD) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    tracesSampleRate: 0.1,
  });
}
```

Add `VITE_SENTRY_DSN` env var to Vercel.

## Todo List
- [ ] Verify RAILWAY_TOKEN GitHub Secret is set
- [ ] Verify VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID GitHub Secrets are set
- [ ] Test backend auto-deploy by pushing a minor change to `backend/`
- [ ] Test frontend auto-deploy by pushing a minor change to `frontend/`
- [ ] Add concurrency control to both workflows
- [ ] Add npm caching to frontend workflow
- [ ] Create UptimeRobot account
- [ ] Add API health monitor (api.5pvietnam.com)
- [ ] Add frontend monitor (5pvietnam.com)
- [ ] Configure alert email notifications
- [ ] (Optional) Set up Sentry project
- [ ] (Optional) Add Sentry SDK to backend
- [ ] (Optional) Add Sentry SDK to frontend

## Success Criteria
- Push to `backend/**` on main triggers Railway deploy (green check in Actions)
- Push to `frontend/**` on main triggers Vercel deploy (green check in Actions)
- UptimeRobot shows both monitors as "UP"
- Receive email alert if a monitor goes down (test by pausing Railway service briefly)

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Railway deploy token expired | Low | High | Token doesn't expire; but check if org access changes |
| Vercel action version breaks | Low | Medium | Pin action versions; test after updates |
| UptimeRobot false positives | Low | Low | Set 2 retry threshold before alerting |

## Security Considerations
- All deploy tokens stored as GitHub encrypted secrets
- Sentry DSN is safe to expose (write-only, no read access to error data)
- UptimeRobot only makes GET requests to public endpoints
- No credentials passed in CI/CD logs

## Next Steps
- After CI/CD and monitoring verified: deployment is complete
- Future improvements:
  - Add pre-deploy CI (lint + test) workflow
  - Add Slack/Telegram notifications for deploy status
  - Migrate backend to Fly.io Singapore for lower latency (Option B)
  - Add Cloudflare CDN in front of Railway for API caching
