# Phase 4: Code Quality & Dependency Management

## Context Links
- Parent: [plan.md](plan.md)
- Depends on: [Phase 2](phase-02-cicd-quality-gate.md)
- Research: [Code Maintenance Report](../reports/researcher-260306-2109-code-maintenance-stability.md)

## Overview
- **Date**: 2026-03-06
- **Priority**: MEDIUM
- **Status**: pending
- **Description**: Setup pre-commit hooks for consistent code quality, configure structured logging for production debugging, and add deployment checklist documentation.

## Key Insights
- Pre-commit hooks catch issues before code reaches CI — faster feedback loop
- Structured logging helps debug production issues without reproducing locally
- Deployment checklist prevents human error during manual deploys
- ruff as pre-commit hook runs in <2 seconds — no developer friction

## Requirements

### Functional
- F1: Pre-commit hooks run ruff + basic checks on every commit
- F2: Structured logging with consistent format across all backend modules
- F3: Deployment checklist documented and accessible
- F4: Dependency vulnerability scanning in CI

### Non-Functional
- NF1: Pre-commit hooks complete in <10 seconds
- NF2: Logging adds <5ms overhead per request
- NF3: No developer workflow disruption

## Related Code Files

### Files to Create
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `backend/app/core/structured_logging_config.py` - Logging configuration (MUST use snake_case, NOT kebab-case — Python cannot import kebab-case modules)
<!-- Updated: Improvement Merge - #2 Fixed file name from kebab-case to snake_case -->

### Files to Modify
- `backend/main.py` - Import structured logging config
- `docs/deployment-guide.md` - Add deployment checklist

## Implementation Steps

1. **Setup pre-commit hooks** (`.pre-commit-config.yaml`)
   ```yaml
   repos:
     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.3.0
       hooks:
         - id: ruff
           args: [--fix, --exit-non-zero-on-fix]
         - id: ruff-format
     - repo: https://github.com/pre-commit/pre-commit-hooks
       rev: v4.5.0
       hooks:
         - id: trailing-whitespace
         - id: end-of-file-fixer
         - id: check-yaml
         - id: check-added-large-files
           args: [--maxkb=1000]
   ```
   - Install: `pip install pre-commit && pre-commit install`
   - Run on all files: `pre-commit run --all-files`

2. **Configure structured JSON logging** (`backend/app/core/structured_logging_config.py`)
   - **Use JSON format** instead of plain text — enables filtering/search in Railway, Datadog, Grafana
   ```python
   import json, logging, sys

   class JSONFormatter(logging.Formatter):
       def format(self, record):
           log_entry = {
               "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
               "level": record.levelname,
               "module": record.name,
               "message": record.getMessage(),
           }
           if record.exc_info:
               log_entry["exception"] = self.formatException(record.exc_info)
           return json.dumps(log_entry, ensure_ascii=False)

   def setup_logging():
       handler = logging.StreamHandler(sys.stdout)
       handler.setFormatter(JSONFormatter())
       logging.basicConfig(level=logging.INFO, handlers=[handler])
       # Reduce noise from third-party libs
       logging.getLogger("httpx").setLevel(logging.WARNING)
       logging.getLogger("httpcore").setLevel(logging.WARNING)
       logging.getLogger("supabase").setLevel(logging.WARNING)
       # IMPORTANT: Never log passwords, tokens, API keys, Authorization headers
   ```
   - Import in `main.py`: `from app.core.structured_logging_config import setup_logging`
   - Call `setup_logging()` before app initialization
<!-- Updated: Improvement Merge - #2 snake_case filename, #8 JSON formatter instead of plain text -->

3. **Add dependency vulnerability scanning to CI**
   - Use `pip-audit` (NOT `safety` — safety v3.0+ requires paid API key)
   - `pip-audit` maintained by PyPA, uses OSV database, free, no registration
   - Add step to CI workflow:
     ```yaml
     - name: Security scan
       run: |
         pip install pip-audit
         pip-audit -r backend/requirements.txt
       continue-on-error: true  # Low-severity doesn't block CI
     ```
<!-- Updated: Improvement Merge - #4 pip-audit instead of safety (no API key needed) -->

4. **Create deployment checklist** (update `docs/deployment-guide.md`)
   - Pre-deploy: tests pass, lint clean, no security alerts
   - Deploy: push to main, verify Railway/Vercel deploy
   - Post-deploy: health check OK, Sentry clean (10 min), response times normal
   - Rollback: Railway redeploy previous version

## Todo List
- [ ] Create `.pre-commit-config.yaml`
- [ ] Install and test pre-commit hooks locally
- [ ] Run `pre-commit run --all-files` to fix existing issues
- [ ] Create structured logging configuration
- [ ] Import logging config in main.py
- [ ] Add safety/pip-audit to CI pipeline
- [ ] Update deployment guide with checklist
- [ ] Document rollback procedure

## Success Criteria
- Pre-commit hooks run on every commit (<10s)
- Structured logs visible in Railway logs dashboard
- Deployment checklist documented and followed
- No known CVEs in dependencies

## Risk Assessment
- **Risk**: Pre-commit hooks annoy developers → **Mitigation**: Keep hooks fast (<10s), only critical checks
- **Risk**: Existing code fails ruff on all files → **Mitigation**: Fix incrementally, use `--fix` for auto-fixable issues
- **Risk**: safety/pip-audit blocks CI for low-severity CVEs → **Mitigation**: Configure severity threshold

## Security Considerations
- Pre-commit hook `check-added-large-files` prevents accidental binary commits
- Dependency scanning catches known vulnerabilities before production
- Structured logging must NOT log sensitive data (passwords, tokens, API keys)

## Next Steps
- Monitor code quality metrics over time
- Consider adding mypy strict mode after team is comfortable
- Evaluate Alembic for database migration safety (future enhancement)
