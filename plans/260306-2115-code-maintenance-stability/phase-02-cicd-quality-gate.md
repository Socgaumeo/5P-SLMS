# Phase 2: CI/CD Quality Gate

## Context Links
- Parent: [plan.md](plan.md)
- Depends on: [Phase 1](phase-01-quick-wins-health-monitoring.md)
- Research: [Code Maintenance Report](../reports/researcher-260306-2109-code-maintenance-stability.md)

## Overview
- **Date**: 2026-03-06
- **Priority**: HIGH
- **Status**: pending
- **Description**: Add GitHub Actions CI pipeline that runs linting (ruff), type checking (mypy), and tests (pytest) before allowing deployment. Blocks broken code from reaching production.

## Key Insights
- Currently no automated checks before deploy — any push to main goes straight to production
- A CI gate prevents ~90% of production rollbacks
- ruff is 10-100x faster than flake8/pylint — ideal for CI
- GitHub Actions free tier provides 2000 min/month for private repos — more than enough

## Requirements

### Functional
- F1: CI pipeline runs on every push to main and every PR
- F2: Linting check with ruff (no syntax errors, no unused imports)
- F3: Type checking with mypy (optional, warning-only initially)
- F4: Test suite with pytest (block on failure)
- F5: Pipeline blocks merge/deploy on failure

### Non-Functional
- NF1: CI pipeline completes in <5 minutes
- NF2: No flaky tests (deterministic results)
- NF3: Clear error messages for failures

## Related Code Files

### Files to Create
- `.github/workflows/ci-quality-gate.yml` - Main CI pipeline
- `backend/pyproject.toml` - ruff + mypy configuration

### Files to Modify
- `backend/requirements.txt` - Add dev dependencies

## Implementation Steps

1. **Create CI workflow** (`.github/workflows/ci-quality-gate.yml`)
   ```yaml
   name: CI Quality Gate
   on:
     push:
       branches: [main]
     pull_request:
       branches: [main]
   jobs:
     # ─── JOB 1: Backend ─────────────────────────────────
     backend:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: '3.12'
             cache: 'pip'  # [#7] Cache pip — lần 2+ chỉ ~15s thay vì 2-3 phút
         - name: Install dependencies
           run: |
             pip install -r backend/requirements.txt
             pip install ruff pytest httpx pytest-asyncio pytest-cov
         - name: Lint with ruff
           run: ruff check backend/
         - name: Type check with mypy
           run: mypy backend/app/ --ignore-missing-imports
           continue-on-error: true  # [#3] Warning only, KHÔNG dùng || true
         - name: Security scan
           run: |
             pip install pip-audit
             pip-audit -r backend/requirements.txt  # [#4] pip-audit thay safety
           continue-on-error: true  # Low-severity không block CI
         - name: Run tests
           run: pytest backend/tests/ -v --tb=short --cov=app --cov-report=term
           env:
             SUPABASE_URL: ${{ secrets.SUPABASE_URL_TEST }}
             SUPABASE_KEY: ${{ secrets.SUPABASE_KEY_TEST }}

     # ─── JOB 2: Frontend ────────────────────────────────
     frontend:  # [#6] Thêm frontend CI
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-node@v4
           with:
             node-version: '20'
             cache: 'npm'
             cache-dependency-path: frontend/package-lock.json
         - name: Install frontend deps
           working-directory: frontend
           run: npm ci
         - name: Lint frontend
           working-directory: frontend
           run: npm run lint
         - name: Build check
           working-directory: frontend
           run: npm run build
   ```
<!-- Updated: Improvement Merge - #3 mypy continue-on-error, #4 pip-audit, #6 frontend CI job, #7 pip cache -->

2. **Configure ruff** (`backend/pyproject.toml`)
   ```toml
   [tool.ruff]
   line-length = 120
   target-version = "py312"
   [tool.ruff.lint]
   select = ["E", "F", "I"]  # errors, pyflakes, isort
   ignore = ["E501"]  # line length (flexible)
   ```

3. **Add dev dependencies** to `backend/requirements.txt`
   - `ruff>=0.3.0`
   - `mypy>=1.8.0`
   - `pytest>=8.0.0`
   - `httpx>=0.27.0` (for async test client)

4. **Enable branch protection** (optional)
   - GitHub → Repo → Settings → Branches → main
   - Require status checks to pass before merging
   - Select "CI Quality Gate" as required check

## Todo List
- [ ] Create `.github/workflows/ci-quality-gate.yml`
- [ ] Create `backend/pyproject.toml` with ruff config
- [ ] Add dev dependencies to requirements.txt
- [ ] Add CI secrets (SUPABASE_URL, SUPABASE_KEY) to GitHub
- [ ] Test: push failing code, verify CI blocks
- [ ] Test: push passing code, verify CI succeeds
- [ ] Optional: Enable branch protection rules

## Success Criteria
- CI runs on every push to main and every PR
- Linting errors block the pipeline
- Test failures block the pipeline
- Pipeline completes in <5 minutes
- Clear error output when pipeline fails

## Risk Assessment
- **Risk**: Existing code has many lint errors → **Mitigation**: Start with minimal rules (E, F only), expand gradually
- **Risk**: Tests need environment variables → **Mitigation**: Add to GitHub Secrets, use test fixtures for DB
- **Risk**: CI too slow → **Mitigation**: Cache pip dependencies, parallel steps

## Security Considerations
- CI secrets stored in GitHub encrypted secrets
- No credentials exposed in CI logs (use `--quiet` flags)
- Branch protection prevents force-push to main

## Next Steps
- Phase 3: Write comprehensive test suite for critical endpoints
