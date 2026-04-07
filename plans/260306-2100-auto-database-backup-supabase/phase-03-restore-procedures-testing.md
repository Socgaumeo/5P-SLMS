# Phase 3: Restore Procedures & Testing

## Context Links
- Parent: [plan.md](plan.md)
- Depends on: [Phase 1](phase-01-supabase-pro-pitr-setup.md), [Phase 2](phase-02-automated-pgdump-backup.md)

## Overview
- **Date**: 2026-03-06
- **Priority**: MEDIUM
- **Status**: pending
- **Description**: Create documented restore procedures for all disaster scenarios, build restore script, test restore on separate instance, create disaster recovery runbook.

## Key Insights
- Untested backups are worthless — must verify restore works
- Three restore scenarios: PITR (Supabase), pg_restore (from dump), manual data recovery
- Restore testing should use a separate Supabase project or local PostgreSQL
- Runbook must be accessible to all team members, not just developer

## Requirements

### Functional
- F1: Restore script from pg_dump backup files
- F2: Documented PITR restore procedure (Supabase dashboard)
- F3: Disaster recovery runbook covering all scenarios
- F4: Tested restore on separate instance at least once

### Non-Functional
- NF1: RTO (Recovery Time Objective) < 1 hour
- NF2: RPO (Recovery Point Objective) < 24 hours
- NF3: Runbook understandable by non-developer team members

## Related Code Files

### Files to Create
- `backend/scripts/restore-database.py` - Restore from pg_dump backup
- `docs/disaster-recovery-runbook.md` - Full recovery documentation

## Implementation Steps

1. **Create restore script** (`backend/scripts/restore-database.py`)
   - Accept backup file path as argument
   - Verify file exists and is valid gzip
   - Decompress and run `pg_restore` against target database
   - Options: `--clean` (drop existing), `--if-exists`, `--no-owner`
   - Safety: require `--confirm` flag to prevent accidental restore
   - Print summary: tables restored, duration, any errors

2. **Test restore on local PostgreSQL**
   - Download latest backup from GitHub Artifacts
   - Restore to local PostgreSQL instance
   - Verify table count, row counts match production
   - Verify critical data integrity (customers, jobs, quotations)

3. **Create disaster recovery runbook** (`docs/disaster-recovery-runbook.md`)
   - **Scenario 1: Accidental data deletion**
     - Use Supabase PITR to restore to before deletion
     - Steps: Dashboard → Backups → Select time → Restore
   - **Scenario 2: Supabase outage**
     - Download latest pg_dump backup
     - Restore to alternative PostgreSQL (local/cloud)
     - Update application DATABASE_URL
   - **Scenario 3: Data corruption**
     - Use PITR to find last clean state
     - Or restore from pg_dump backup
   - **Scenario 4: Complete project loss**
     - Create new Supabase project
     - Restore from pg_dump backup
     - Reconfigure environment variables
   - Include contact info, escalation paths, expected recovery times

4. **Schedule quarterly restore test**
   - Add calendar reminder to test restore every 3 months
   - Document test results each time

## Todo List
- [ ] Create `backend/scripts/restore-database.py` script
- [ ] Test restore on local PostgreSQL instance
- [ ] Verify restored data integrity (table counts, critical data)
- [ ] Create `docs/disaster-recovery-runbook.md`
- [ ] Document all 4 disaster scenarios with step-by-step instructions
- [ ] Share runbook with team
- [ ] Schedule quarterly restore test reminder

## Success Criteria
- Restore script works end-to-end on test instance
- Restored data matches production (table counts, row counts)
- Runbook covers 4 disaster scenarios with clear steps
- Team members can follow runbook without developer assistance
- RTO < 1 hour demonstrated in test

## Risk Assessment
- **Risk**: Restore script accidentally runs on production → **Mitigation**: Require `--confirm` flag + target URL validation
- **Risk**: Runbook becomes outdated → **Mitigation**: Review quarterly during restore test

## Security Considerations
- Restore script must never hardcode database credentials
- Backup files should be treated as sensitive data
- Restore testing should use separate instance, never production

## Next Steps
- Monitor backup success rate over time
- Consider automated restore testing (future enhancement)
