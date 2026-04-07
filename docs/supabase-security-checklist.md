# Supabase Security Checklist for 5P-SLMS

## Project Info
- **Project ID:** ooixntyflwmjaryxwakx
- **Region:** Singapore (ap-southeast-1)
- **Dashboard:** https://supabase.com/dashboard/project/ooixntyflwmjaryxwakx

## 1. Row Level Security (RLS) - CRITICAL

### Current Status: ✅ ENABLED (2026-02-12)
RLS policies applied via `backend/scripts/enable-rls-policies.sql`

### Tables Status:
| Table | RLS Status | Access |
|-------|------------|--------|
| users | ✅ Enabled | service_role only |
| customers | ✅ Enabled | service_role only |
| vendors | ✅ Enabled | service_role only |
| jobs | ✅ Enabled | service_role only |
| job_services | ✅ Enabled | service_role only |
| job_costs | ✅ Enabled | service_role only |
| vendor_rates | ✅ Enabled | service_role only |
| customer_rates | ✅ Enabled | service_role only |
| activity_logs | ✅ Enabled | service_role only |
| master_statuses | ✅ Enabled | anon: READ, service_role: ALL |
| master_service_types | ✅ Enabled | anon: READ, service_role: ALL |
| master_vehicle_types | ✅ Enabled | anon: READ, service_role: ALL |
| master_routes | ✅ Enabled | anon: READ, service_role: ALL |

### Note on Backend Access
Backend uses psycopg2 with postgres superuser (bypasses RLS).
This is correct - backend has full database access.

## 2. Backups

### Automatic Backups (Free Plan)
- ✅ Daily backups (7 days retention)
- Included by default on all plans

### Point-in-Time Recovery (PITR)
- ❌ Requires Pro plan ($25/month)
- Enables recovery to any point in time
- Recommended for production

### Manual Backup:
```bash
# Export using migration script
cd backend/scripts
python3 migrate-supabase-mumbai-to-singapore.py
# Backup saved to /tmp/supabase_backup_YYYYMMDD_HHMMSS.json
```

## 3. API Keys Security

### Service Role Key
- **Usage:** Backend server only
- **NEVER expose in frontend code**
- **Current:** Stored in .env (✅ gitignored)

### Anon Key
- **Usage:** Public/frontend
- **Protected by RLS policies**
- **Current:** Used for read-only master data

## 4. Connection Security

### SSL/TLS
- ✅ Enabled by default (Supabase enforces SSL)

### Connection Pooler
- ✅ Using pooler endpoint (port 6543)
- Good for serverless/many connections

## 5. Additional Recommendations

### Enable in Supabase Dashboard:

1. **Auth → Settings:**
   - Enable email confirmation
   - Set secure password requirements
   - Configure session timeout

2. **Database → Extensions:**
   - Consider enabling `pgcrypto` for password hashing
   - Enable `uuid-ossp` for UUIDs

3. **Settings → API:**
   - Review exposed schemas
   - Consider limiting RPC functions

4. **Settings → Auth:**
   - Disable signup if not needed
   - Configure redirect URLs

## 6. Monitoring

### Supabase Dashboard:
- Database → Reports (query performance)
- Logs (API access logs)
- Usage (bandwidth, storage)

### Set Up Alerts:
- Database storage > 80%
- API rate limits
- Auth failures

## Action Items

- [x] Run RLS script in SQL Editor (Done 2026-02-12)
- [x] Verify RLS enabled on all tables (Done 2026-02-12)
- [ ] Consider upgrading to Pro for PITR
- [ ] Review API key exposure in code
- [ ] Set up monitoring alerts
