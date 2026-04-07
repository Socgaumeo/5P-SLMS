# Phase 1: Supabase Pro + PITR Setup

## Context Links
- Parent: [plan.md](plan.md)
- Dependencies: None (foundation phase)
- Research: [Backup Strategies Report](../reports/researcher-260306-2109-supabase-backup-strategies.md)

## Overview
- **Date**: 2026-03-06
- **Priority**: HIGH
- **Status**: pending
- **Description**: Upgrade Supabase to Pro plan, enable Point-in-Time Recovery (PITR), verify backup functionality, and test basic restore.

## Key Insights
- Supabase Free plan only has 7-day daily backup retention, no PITR
- Pro plan ($25/month) enables 28-day PITR — restore to any second
- PITR uses WAL (Write-Ahead Log) archiving — automatic once Pro enabled
- For <1GB database, Pro plan is the most cost-effective disaster recovery

## Requirements

### Functional
- F1: Upgrade Supabase project to Pro plan
- F2: Enable and verify PITR in Supabase dashboard
- F3: Test restore from daily backup snapshot
- F4: Document backup coverage and retention policy

### Non-Functional
- NF1: Zero downtime during upgrade
- NF2: PITR window covers minimum 28 days
- NF3: Monthly cost stays under $30

## Implementation Steps

1. **Upgrade Supabase to Pro plan**
   - Go to Supabase Dashboard → Project → Settings → Billing
   - Upgrade to Pro plan ($25/month)
   - Verify all features activated (PITR, 14-day backup retention)

2. **Enable PITR**
   - Dashboard → Database → Backups → Enable PITR
   - Verify WAL archiving is active
   - Note: PITR may take a few hours to fully initialize

3. **Verify backup status**
   - Check Dashboard → Database → Backups → see daily snapshots
   - Confirm PITR timeline shows recent data
   - Record backup schedule and retention window

4. **Test restore (read-only)**
   - Use Dashboard → Backups → Preview restore point
   - Do NOT actually restore on production — just verify the option works
   - Document the restore UI flow for team reference

5. **Document backup policy**
   - Create section in disaster recovery runbook
   - Include: backup schedule, retention window, PITR window, restore steps
   - Include Supabase support contact for escalation

## Todo List
- [ ] Upgrade Supabase to Pro plan ($25/month)
- [ ] Enable PITR in Supabase dashboard
- [ ] Verify daily backup snapshots visible
- [ ] Verify PITR timeline active
- [ ] Test restore preview (read-only, don't actually restore)
- [ ] Document backup policy and retention windows

## Success Criteria
- Pro plan active with PITR enabled
- Daily backup snapshots visible in dashboard
- PITR timeline shows recent 28 days of data
- Backup policy documented

## Risk Assessment
- **Risk**: Upgrade causes downtime → **Mitigation**: Supabase plan upgrades are zero-downtime
- **Risk**: PITR not available in current region → **Mitigation**: Check region compatibility before upgrade

## Security Considerations
- Supabase handles encryption at rest for all backups
- PITR data stored in same region as primary database
- Access to backup/restore requires Supabase dashboard admin access

## Next Steps
- Phase 2: Automated pg_dump for additional backup layer
