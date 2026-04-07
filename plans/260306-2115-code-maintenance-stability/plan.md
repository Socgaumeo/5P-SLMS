---
title: "Code Maintenance & Stability"
description: "Automated testing, error monitoring, CI/CD gates, and code quality for production stability"
status: pending
priority: P1
effort: 10h
branch: main
tags: [maintenance, stability, testing, ci-cd, monitoring]
created: 2026-03-06
---

# Code Maintenance & Stability

## Goal
Establish automated testing, error monitoring, CI/CD quality gates, and code quality tools to prevent production regressions, catch bugs early, and maintain long-term code health.

## Approach
- Quick wins first: health checks, Sentry, Dependabot
- CI/CD gate: automated linting + tests before deploy
- Gradual test coverage increase (target 70%+ critical paths)
- Pre-commit hooks for consistent code quality

## Current State
- No automated test runs in CI/CD
- No error monitoring (crashes may go unnoticed)
- No staging environment
- Manual deployment via Railway/Vercel
- Minimal logging for debugging

## Phases

| # | Phase | Priority | Effort | Status |
|---|-------|----------|--------|--------|
| 1 | [Quick Wins: Health Checks + Monitoring](phase-01-quick-wins-health-monitoring.md) | HIGH | 2h | pending |
| 2 | [CI/CD Quality Gate](phase-02-cicd-quality-gate.md) | HIGH | 3h | pending |
| 3 | [Automated Testing Suite](phase-03-automated-testing-suite.md) | HIGH | 3h | pending |
| 4 | [Code Quality & Dependency Management](phase-04-code-quality-dependency-management.md) | MEDIUM | 2h | pending |

## Key Files (New/Modified)
- `.github/workflows/ci.yml` - CI/CD pipeline with quality gates
- `backend/tests/conftest.py` - Shared test fixtures
- `backend/tests/test_auth.py` - Auth endpoint tests
- `backend/tests/test_jobs.py` - Job endpoint tests
- `backend/tests/test_chat.py` - Chat endpoint tests
- `.pre-commit-config.yaml` - Pre-commit hooks config
- `docs/disaster-recovery-runbook.md` - Deployment + recovery docs

## Dependencies
- Sentry (free tier: 5K events/month)
- Uptime Robot (free tier) or similar
- GitHub Actions (already available)
- pytest, httpx, ruff, mypy (Python packages)

## Risks
- Test writing takes time away from features → focus on critical paths only
- Sentry free tier may not be enough → monitor usage, upgrade if needed
- Pre-commit hooks slow down commits → keep hooks fast (<10s)

## Success Criteria
- CI/CD gate blocks broken code from deploying
- 70%+ test coverage on critical API routes (auth, jobs, chat)
- Sentry captures and alerts on production errors
- Health check endpoint monitored every 5 minutes
- Pre-commit hooks prevent common issues (syntax, linting)

## Research
- [Code Maintenance Stability Report](../reports/researcher-260306-2109-code-maintenance-stability.md)

## Improvement Merge Log — 2026-03-06

**Source:** CodeMaintenance_Improvement.docx (Claude review of original plan)
**Issues found:** 8 (2 critical bugs, 3 security/issues, 3 missing features)

| # | Issue | Severity | Phase | Fix Applied |
|---|-------|----------|-------|-------------|
| 1 | Test file names `test-*.py` → pytest won't discover | 🔴 BUG | Phase 3 | Renamed to `test_*.py` + added pytest config |
| 2 | `structured-logging-config.py` → Python can't import | 🔴 BUG | Phase 4 | Renamed to `structured_logging_config.py` |
| 3 | `mypy || true` makes type check useless | 🟡 ISSUE | Phase 2 | Changed to `continue-on-error: true` |
| 4 | `safety check` needs API key since v3.0 | 🟡 ISSUE | Phase 4 | Replaced with `pip-audit` (free, no key) |
| 5 | Health check leaks `str(e)` internal errors | 🟡 SECURITY | Phase 1 | Sanitized response, log server-side only |
| 6 | CI doesn't cover frontend (React/JSX) | 🔵 MISSING | Phase 2 | Added frontend job (npm ci, lint, build) |
| 7 | CI doesn't cache pip → 2-3 min install | 🔵 MISSING | Phase 2 | Added `cache: 'pip'` to setup-python |
| 8 | Logging plain text → not queryable | 🔵 MISSING | Phase 4 | JSON formatter for Railway/Datadog |

**Additional improvements:**
- Added `/health/live` endpoint for load balancer
- Added mock Supabase fixture pattern for test isolation
- Added pre-check step: verify `app` export in `main.py` before writing tests
- Added `pytest-asyncio` with `asyncio_mode = "auto"` for async test support
