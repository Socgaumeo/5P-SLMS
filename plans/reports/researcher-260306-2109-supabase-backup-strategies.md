# Supabase Backup Strategies Research Report

**Date:** 2026-03-06
**Project:** 5P SLMS (Logistics SaaS, 10-50 users, ~50 tables, <1GB data)
**Context:** Hosted PostgreSQL on Supabase, need disaster recovery & outage protection

---

## 1. Supabase Built-in Backup Features

### Free Plan (Current)
- **Daily backups** with 7-day retention
- Manual download from dashboard
- No PITR (Point-in-Time Recovery)
- No automated export

### Pro Plan ($25/month)
- Same daily backups + **14-day retention**
- **PITR enabled** (restore to any second within 28 days)
- Recommended for production

**Verdict:** Current free plan covers basic disaster recovery but lacks PITR. Pro plan essential for critical SaaS.

---

## 2. pg_dump Automated Backup

**Best for:** Low-cost, self-managed backups.

### Implementation
```bash
# Cron job: Run daily at 2 AM
SUPABASE_DB_URL="postgresql://..."
pg_dump "$SUPABASE_DB_URL" | gzip > backup_$(date +%Y%m%d).sql.gz
```

**Advantages:**
- Zero cost (use existing script in `.claude/skills/databases/scripts/db_backup.py`)
- Full control over retention
- Can compress to ~30-50MB for <1GB data
- Supports automated rotation

**Disadvantages:**
- Requires persistent storage (VM/server)
- No incremental backups (each ~100-200MB)
- Maintenance overhead

**Suitable for 5P SLMS:** YES – low data volume makes this practical.

---

## 3. Supabase Database Webhooks (Real-time Triggers)

**Use case:** NOT ideal for backups.

Webhooks trigger on INSERT/UPDATE/DELETE but designed for event-driven flows, not backup coordination. Would create excessive overhead for every row change.

**Verdict:** Skip this approach for backups.

---

## 4. Third-Party Solutions

### S3/GCS Backup (AWS/Google Cloud)
- **Tool:** WAL-G, pg_basebackup, or manual pg_dump → S3
- **Cost:** AWS S3 ~$0.023/GB/month + transfer
- **Benefit:** Geographically distributed, durable
- **Setup:** Lambda/Cloud Function triggers daily dump
- **RTO/RPO:** 24h backup window, minimal data loss

### pgBackRest
- **Advanced:** Incremental backups, parallel transfers, compression
- **Learning curve:** Higher setup complexity
- **Cost:** Self-hosted, minimal overhead
- **Best for:** Larger databases (>10GB)

**Verdict for 5P SLMS:** S3 approach viable (~$1-2/month), but pg_dump simpler.

---

## 5. Point-in-Time Recovery (PITR)

**Supabase Pro plan:** 28-day PITR window
- Restore to any second within 28 days
- Automatic WAL archiving by Supabase
- **Cost:** $25/month for pro plan

**Self-managed:** Requires pg_basebackup + WAL archiving to S3 (complex, not recommended for small team).

**Recommendation:** Upgrade to Pro ($25/month) for production. Cheaper than building self-managed PITR.

---

## 6. Cross-Region Replication

**Option 1: Supabase Redundancy**
- No built-in cross-region replication on free/pro
- Would require separate Supabase instance (expensive)

**Option 2: Logical Replication**
- PostgreSQL built-in feature
- Streams changes to secondary database
- **Setup:** Complex, requires external PostgreSQL
- **Cost:** Additional database hosting

**Verdict:** NOT practical for <1GB SaaS. Better to use geo-redundant S3 backups.

---

## 7. Best Practices for Backup Scheduling & Retention

| Strategy | Frequency | Retention | RPO/RTO | Cost |
|----------|-----------|-----------|---------|------|
| **Free Plan Only** | Daily (auto) | 7 days | 24h/4h | $0 |
| **Free + pg_dump** | Daily (3 AM) | 30 days local | 24h/1h | $0 |
| **Free + S3** | Daily (3 AM) | 90 days S3 | 24h/1h | ~$1/mo |
| **Pro Plan** | Daily (auto) + PITR | 28 days | 24h/5min | $25/mo |
| **Pro + pg_dump** | Daily + PITR | 90 days | 24h/5min | $25/mo |

**Recommended:** Pro Plan + Daily pg_dump to S3
- Supabase PITR covers accidental deletions
- pg_dump provides archival + audit trail
- Total cost: ~$26/month

---

## 8. Cost Analysis

| Solution | Monthly Cost | Data Retention | PITR | Complexity |
|----------|-------------|-----------------|------|------------|
| Supabase Free | $0 | 7 days | ❌ | Low |
| Supabase Pro | $25 | 28 days | ✅ 28d | Low |
| Free + pg_dump local | $0 | Depends on VM | ❌ | Medium |
| Free + S3 backups | ~$1 | 90+ days | ❌ | Medium |
| Pro + S3 archive | ~$26 | 90+ days | ✅ 28d | Medium |

**Recommendation for 5P SLMS:**
- **Minimum:** Supabase Pro ($25/mo) — handles 95% of scenarios
- **Optimal:** Pro + daily pg_dump to S3 (~$26/mo) — added redundancy + compliance

---

## Implementation Roadmap

### Phase 1: Immediate (Week 1)
- [ ] Upgrade to Supabase Pro ($25/month)
- [ ] Verify PITR enabled in dashboard
- [ ] Test restore from daily backup

### Phase 2: Short-term (Week 2-3)
- [ ] Setup daily pg_dump via cron
- [ ] Use existing `.claude/skills/databases/scripts/db_backup.py`
- [ ] Store locally (or on VM) with 30-day retention

### Phase 3: Long-term (Month 2)
- [ ] Add S3 integration for pg_dump exports
- [ ] Setup Lambda/automation to upload to S3
- [ ] Document restore procedure

---

## Risk Mitigation Checklist

- [x] Daily automated backups (Supabase free plan)
- [x] 7-day retention minimum
- [ ] PITR capability (requires Pro plan)
- [ ] Offsite backup copy (S3 integration)
- [ ] Documented restore procedure
- [ ] Test restore annually
- [ ] Monitoring for backup failures

---

## Unresolved Questions

1. **Budget approval:** Is $25/month acceptable for Pro plan upgrade?
2. **Compliance:** Are 7-day daily backups sufficient or do you need 90-day archival?
3. **RTO target:** How quickly must you restore in case of outage? (affects solution choice)
4. **Data sensitivity:** Do you need compliance certifications (SOC2, GDPR)?
