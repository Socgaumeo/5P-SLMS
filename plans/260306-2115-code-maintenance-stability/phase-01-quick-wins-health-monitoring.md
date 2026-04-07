# Phase 1: Quick Wins — Health Checks + Error Monitoring

## Context Links
- Parent: [plan.md](plan.md)
- Dependencies: None (foundation phase)
- Research: [Code Maintenance Report](../reports/researcher-260306-2109-code-maintenance-stability.md)

## Overview
- **Date**: 2026-03-06
- **Priority**: HIGH
- **Status**: pending
- **Description**: Add enhanced health check endpoint, integrate Sentry error monitoring, setup Uptime Robot for external monitoring, and enable Dependabot security alerts.

## Key Insights
- Current health endpoint exists but doesn't check DB connectivity
- Sentry free tier (5K events/month) sufficient for our scale
- Uptime Robot free tier monitors every 5 minutes — enough for production
- These are highest-ROI items: <2 hours total, prevents silent failures

## Requirements

### Functional
- F1: `/health/ready` endpoint checks DB connectivity, returns 503 if unhealthy
- F2: Sentry captures all unhandled exceptions + slow requests
- F3: Uptime Robot pings health endpoint every 5 minutes, alerts on failure
- F4: Dependabot alerts enabled for known CVEs in dependencies

### Non-Functional
- NF1: Health check responds in <500ms
- NF2: Sentry SDK adds <10ms overhead per request
- NF3: No false positive alerts (health check must be reliable)

## Related Code Files

### Files to Modify
- `backend/main.py` - Add Sentry initialization + enhanced health endpoint
- `backend/requirements.txt` - Add sentry-sdk dependency

### Files to Read (Reference)
- `backend/app/db/supabase_client.py` - Supabase client for DB check

## Implementation Steps

1. **Enhance health check endpoint** (`backend/main.py`)
   - **SECURITY**: Never expose internal error details in public endpoint response
   - Log error detail server-side, return sanitized response to client
   ```python
   import logging
   logger = logging.getLogger(__name__)

   @app.get("/health/ready")
   async def health_ready():
       try:
           # Check Supabase DB connectivity
           result = supabase.table("customers").select("customer_id").limit(1).execute()
           return {"status": "ready", "db": "connected", "timestamp": datetime.utcnow().isoformat()}
       except Exception as e:
           # Log full error detail server-side (visible in Railway logs)
           logger.error(f"DB health check failed: {e}")
           # Return sanitized response — no internal details exposed
           return JSONResponse(
               status_code=503,
               content={"status": "unhealthy", "db": "unavailable", "timestamp": datetime.utcnow().isoformat()}
           )
   ```
   - Also add `/health/live` endpoint (simple 200 OK for load balancer):
   ```python
   @app.get("/health/live")
   async def health_live():
       return {"status": "alive"}
   ```
<!-- Updated: Improvement Merge - #5 Sanitize health check error response, add /health/live -->

2. **Integrate Sentry SDK**
   - Add `sentry-sdk[fastapi]` to `requirements.txt`
   - Initialize in `main.py`:
     ```python
     import sentry_sdk
     sentry_sdk.init(
         dsn=os.getenv("SENTRY_DSN"),
         traces_sample_rate=0.1,  # 10% of requests traced
         environment=os.getenv("ENVIRONMENT", "production"),
     )
     ```
   - Add `SENTRY_DSN` to Railway environment variables
   - Verify errors appear in Sentry dashboard

3. **Setup Uptime Robot**
   - Create account at uptimerobot.com (free)
   - Add monitor: HTTP(s), URL = `https://api.5pvietnam.com/health/ready`
   - Interval: 5 minutes
   - Alert contacts: admin email
   - Alert on 2 consecutive failures (avoid false positives)

4. **Enable Dependabot**
   - GitHub → Repo → Settings → Code Security → Enable Dependabot alerts
   - Optionally add `.github/dependabot.yml`:
     ```yaml
     version: 2
     updates:
       - package-ecosystem: "pip"
         directory: "/backend"
         schedule:
           interval: "weekly"
     ```

## Todo List
- [ ] Enhance `/health/ready` endpoint with DB connectivity check
- [ ] Add `sentry-sdk[fastapi]` to requirements.txt
- [ ] Initialize Sentry SDK in main.py
- [ ] Add SENTRY_DSN to Railway environment variables
- [ ] Verify errors captured in Sentry dashboard
- [ ] Setup Uptime Robot monitor for health endpoint
- [ ] Enable Dependabot alerts in GitHub settings
- [ ] Test: trigger error, verify appears in Sentry
- [ ] Test: stop DB, verify health endpoint returns 503

## Success Criteria
- `/health/ready` returns 200 when DB is up, 503 when DB is down
- Sentry captures unhandled exceptions within 30 seconds
- Uptime Robot alerts within 10 minutes of downtime
- Dependabot creates PRs for known vulnerabilities

## Risk Assessment
- **Risk**: Sentry free tier exceeded → **Mitigation**: 5K events/month is generous for our traffic; add rate limiting if needed
- **Risk**: Health check itself causes load → **Mitigation**: Simple SELECT with LIMIT 1, minimal overhead
- **Risk**: Too many Dependabot PRs → **Mitigation**: Set weekly schedule, review in batch

## Security Considerations
- Sentry DSN stored in Railway environment (not in code)
- Health endpoint exposes no sensitive data (only status + timestamp)
- Dependabot PRs require manual merge (no auto-merge)

## Next Steps
- Phase 2: CI/CD quality gate to prevent broken deploys
