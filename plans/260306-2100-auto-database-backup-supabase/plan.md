---
title: "Auto Database Backup & Disaster Recovery"
description: "Automated Supabase backup with pg_dump, PITR, and restore procedures"
status: pending
priority: P1
effort: 6h
branch: main
tags: [database, backup, disaster-recovery, supabase]
created: 2026-03-06
---

# Auto Database Backup & Disaster Recovery

## Goal
Protect 5P SLMS data against Supabase outages, accidental deletion, and data corruption through automated backup strategies with documented restore procedures.

## Approach
- Upgrade Supabase to Pro plan for PITR (Point-in-Time Recovery)
- Automated daily pg_dump backups with local + cloud storage
- Documented restore procedures for all disaster scenarios
- Monitoring and alerting for backup failures

## Current State
- Supabase Free plan: daily backups, 7-day retention, no PITR
- No automated external backups
- No documented restore procedure
- ~50 tables, <1GB data

## Phases

| # | Phase | Priority | Effort | Status |
|---|-------|----------|--------|--------|
| 1 | [Supabase Pro + PITR Setup](phase-01-supabase-pro-pitr-setup.md) | HIGH | 1h | pending |
| 2 | [Automated pg_dump Backup Script](phase-02-automated-pgdump-backup.md) | HIGH | 3h | pending |
| 3 | [Restore Procedures & Testing](phase-03-restore-procedures-testing.md) | MEDIUM | 2h | pending |

## Key Files (New)
- `backend/scripts/backup-database.py` - Daily pg_dump automation
- `backend/scripts/restore-database.py` - Restore from backup
- `docs/disaster-recovery-runbook.md` - Restore procedures

## Dependencies
- Supabase PostgreSQL (existing)
- Supabase Pro plan ($25/month) for PITR
- Cloud storage (S3/GCS) for offsite backups (optional, ~$1/month)

## Risks
- Budget: Pro plan costs $25/month → justified for production SaaS
- pg_dump requires persistent server → use Railway cron or GitHub Actions
- Restore testing may cause downtime → test on separate instance

## Success Criteria
- Daily automated backups running with 30-day retention
- PITR enabled with 28-day window
- Documented restore procedure tested at least once
- Backup failure alerts configured
- RPO < 24 hours, RTO < 1 hour

## Research
- [Supabase Backup Strategies Report](../reports/researcher-260306-2109-supabase-backup-strategies.md)
