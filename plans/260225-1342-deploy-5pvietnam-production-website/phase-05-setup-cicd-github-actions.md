# Phase 05: Setup CI/CD with GitHub Actions

## Context Links

- [plan.md](plan.md) - Overview
- [phase-02](phase-02-deploy-frontend-to-vercel.md) - Vercel deploy
- [phase-03](phase-03-deploy-backend-to-railway.md) - Railway deploy

## Overview

- **Priority**: P2
- **Status**: pending
- **Effort**: 45m
- **Description**: Create GitHub Actions workflows for automated testing + deployment with path-based triggers

## Key Insights

- Vercel has built-in GitHub integration (auto-deploys on push) - workflow is for lint/test only
- Railway also has GitHub auto-deploy - workflow is for pre-deploy validation
- Path-based triggers prevent unnecessary builds (frontend changes don't trigger backend CI)
- No existing tests or CI/CD in the project - start simple, iterate
- GitHub Actions free tier: 2000 min/mo for private repos, unlimited for public

## Requirements

### Functional
- Push to `main` on `frontend/**` triggers frontend lint + build check
- Push to `main` on `backend/**` triggers backend lint + health check
- Both Vercel and Railway auto-deploy from main (platform-native integration)
- Failed CI shows red status on GitHub commits/PRs

### Non-Functional
- CI runs < 3 minutes
- No secrets leaked in CI logs
- Minimal workflow maintenance burden

## Architecture

```
GitHub Push to main
├── frontend/** changed
│   └── .github/workflows/ci-frontend.yml
│       ├── npm install
│       ├── npm run lint
│       ├── npm run build (verify no build errors)
│       └── Vercel auto-deploys (separate, platform-native)
│
└── backend/** changed
    └── .github/workflows/ci-backend.yml
        ├── pip install -r requirements.txt
        ├── python -m py_compile main.py (syntax check)
        ├── docker build --target test (if applicable)
        └── Railway auto-deploys (separate, platform-native)
```

## Related Code Files

### Files to Create
- `.github/workflows/ci-frontend.yml`
- `.github/workflows/ci-backend.yml`

### Files to Verify
- `frontend/package.json` - has `lint` and `build` scripts
- `backend/requirements.txt` - has all deps

## Implementation Steps

### 1. Create Frontend CI Workflow

Create `.github/workflows/ci-frontend.yml`:

```yaml
name: Frontend CI

on:
  push:
    branches: [main]
    paths: ['frontend/**']
  pull_request:
    branches: [main]
    paths: ['frontend/**']

jobs:
  lint-and-build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - run: npm ci

      - name: Lint
        run: npm run lint

      - name: Build
        run: npm run build
        env:
          VITE_API_URL: https://api.5pvietnam.com
```

### 2. Create Backend CI Workflow

Create `.github/workflows/ci-backend.yml`:

```yaml
name: Backend CI

on:
  push:
    branches: [main]
    paths: ['backend/**']
  pull_request:
    branches: [main]
    paths: ['backend/**']

jobs:
  lint-and-check:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
          cache-dependency-path: backend/requirements.txt

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Syntax check
        run: python -m compileall app/ main.py -q

      - name: Docker build test
        run: docker build -t slms-backend-test .
```

### 3. Configure GitHub Secrets

Go to GitHub repo > Settings > Secrets and variables > Actions:

| Secret | Purpose | Where to get |
|--------|---------|--------------|
| `VERCEL_TOKEN` | Vercel API (if using CLI deploy) | Vercel Settings > Tokens |
| `RAILWAY_TOKEN` | Railway API (if using CLI deploy) | Railway Settings > Tokens |

**Note**: If relying on Vercel/Railway GitHub integrations (recommended), these tokens are NOT needed. The platforms deploy directly from GitHub webhooks.

### 4. Connect Vercel to GitHub (Platform Integration)

1. Vercel Dashboard > Project > Settings > Git
2. Ensure "Auto-deploy" is enabled for `main` branch
3. Ensure Root Directory is `frontend`
4. Vercel listens to GitHub webhooks - no Action needed for deploy

### 5. Connect Railway to GitHub (Platform Integration)

1. Railway Dashboard > Service > Settings
2. Ensure "Auto-deploy" is enabled
3. Source branch: `main`
4. Root Directory: `backend`
5. Railway listens to GitHub webhooks - no Action needed for deploy

### 6. Test the Workflows

```bash
# Make a trivial frontend change and push
echo "// CI test" >> frontend/vite.config.js
git add frontend/vite.config.js
git commit -m "ci: test frontend workflow"
git push origin main

# Check Actions tab on GitHub for green/red status
# Revert the test change
```

## Todo List

- [ ] Create `.github/workflows/ci-frontend.yml`
- [ ] Create `.github/workflows/ci-backend.yml`
- [ ] Ensure `npm run lint` works locally (fix lint errors if any)
- [ ] Ensure `python -m compileall` passes locally
- [ ] Verify Vercel GitHub integration auto-deploys
- [ ] Verify Railway GitHub integration auto-deploys
- [ ] Push and verify both CI workflows run green
- [ ] Optionally add GitHub secrets for Vercel/Railway tokens

## Success Criteria

- Frontend CI: green on push to `frontend/**`
- Backend CI: green on push to `backend/**`
- Changes to `backend/**` do NOT trigger frontend CI (and vice versa)
- Vercel auto-deploys after frontend CI passes
- Railway auto-deploys after backend CI passes
- PR checks show CI status before merge

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| npm ci fails (no lock file) | Medium | Low | Run `npm install` to generate `package-lock.json` first |
| Lint errors block CI | Medium | Low | Fix lint errors or adjust ESLint config |
| Docker build fails in CI | Low | Low | Test locally first |
| Auto-deploy race condition | Very Low | Low | CI and deploy are independent; no conflict |

## Security Considerations

- **No secrets in workflows**: Vercel/Railway deploy via GitHub webhooks, not CI
- **Secrets storage**: If tokens needed, use GitHub encrypted secrets only
- **No .env in CI**: Backend syntax check doesn't need runtime env vars
- **PR checks**: CI runs on PRs before merge to main (catches errors early)

## Next Steps

- Phase 06: Production hardening (security headers, monitoring)
- Consider adding integration tests in future iteration
