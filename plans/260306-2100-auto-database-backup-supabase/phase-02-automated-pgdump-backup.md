# Phase 2: Automated pg_dump Backup Script

## Context Links
- Parent: [plan.md](plan.md)
- Depends on: [Phase 1](phase-01-supabase-pro-pitr-setup.md)
- Research: [Backup Strategies Report](../reports/researcher-260306-2109-supabase-backup-strategies.md)

## Overview
- **Date**: 2026-03-06
- **Priority**: HIGH
- **Status**: pending
- **Description**: Create automated daily pg_dump backup script that runs via GitHub Actions, compresses and stores backups locally + optionally to S3, with 30-day retention.

## Key Insights
- pg_dump for <1GB database produces ~30-50MB compressed files
- GitHub Actions can run scheduled cron jobs (free for public repos, 2000 min/month for private)
- Railway cron alternative if GitHub Actions minutes are limited
- Supabase connection string available from project settings

## Requirements

### Functional
- F1: Daily automated pg_dump at 3:00 AM UTC
- F2: Compress backup with gzip (target <50MB per backup)
- F3: 30-day local retention with automatic rotation
- F4: Optional S3 upload for offsite storage
- F5: Failure notification via GitHub Actions / email

### Non-Functional
- NF1: Backup completes in <5 minutes
- NF2: No impact on production database performance
- NF3: Backup files encrypted or stored securely

## Architecture

### Backup Flow
```
GitHub Actions Cron (3 AM UTC daily)
        |
        v
  Run backup-database.py
        |
        v
  pg_dump → gzip → backup_YYYYMMDD.sql.gz
        |
        v
  Upload to GitHub Artifacts (30-day retention)
        |
        v (optional)
  Upload to S3 (90-day retention)
        |
        v
  Cleanup old backups (>30 days)
        |
        v
  Send notification (success/failure)
```

## Related Code Files

### Files to Create
- `backend/scripts/backup-database.py` - pg_dump automation script
- `.github/workflows/daily-database-backup.yml` - Cron workflow

### Files to Read (Reference)
- `backend/app/core/config.py` - Database connection string

## Implementation Steps

1. **Create backup script** (`backend/scripts/backup-database.py`)
   - Read database URL from environment variable `DATABASE_URL`
   - Run `pg_dump` with `--format=custom` for best compression
   - Compress output with gzip
   - Filename format: `backup_5pslms_YYYYMMDD_HHMMSS.sql.gz`
   - Verify backup file size > 0 (sanity check)
   - Print summary: file size, table count, duration

2. **Create GitHub Actions workflow** (`.github/workflows/daily-database-backup.yml`)
   ```yaml
   name: Daily Database Backup
   on:
     schedule:
       - cron: '0 3 * * *'  # 3 AM UTC daily
     workflow_dispatch: {}  # Manual trigger
   jobs:
     backup:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - name: Install PostgreSQL client
           run: sudo apt-get install -y postgresql-client
         - name: Run backup
           env:
             DATABASE_URL: ${{ secrets.SUPABASE_DB_URL }}
           run: python backend/scripts/backup-database.py
         - name: Upload artifact
           uses: actions/upload-artifact@v4
           with:
             name: db-backup-${{ github.run_id }}
             path: backups/*.sql.gz
             retention-days: 30
   ```

3. **Add Supabase DB URL to GitHub Secrets**
   - Go to GitHub → Repo → Settings → Secrets
   - Add `SUPABASE_DB_URL` with direct PostgreSQL connection string
   - Format: `postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres`

4. **Optional: S3 upload step**
   - Add AWS credentials to GitHub Secrets
   - Use `aws s3 cp` to upload to S3 bucket
   - S3 lifecycle policy: delete after 90 days

5. **Test backup manually**
   - Run workflow via `workflow_dispatch`
   - Verify artifact uploaded
   - Download and test restore locally

## Todo List
- [ ] Create `backend/scripts/backup-database.py` script
- [ ] Create `.github/workflows/daily-database-backup.yml` workflow
- [ ] Add `SUPABASE_DB_URL` to GitHub Secrets
- [ ] Test manual workflow dispatch
- [ ] Verify backup artifact uploaded and downloadable
- [ ] Test restore from backup file locally
- [ ] Optional: Add S3 upload step

## Success Criteria
- Daily backup runs automatically at 3 AM UTC
- Backup file size > 0 and < 100MB
- 30-day retention via GitHub Artifacts
- Manual trigger works for on-demand backups
- Backup failure sends notification

## Risk Assessment
- **Risk**: GitHub Actions minutes exceed free tier → **Mitigation**: Backup takes <2 min, well within 2000 min/month
- **Risk**: Database URL exposed → **Mitigation**: Stored in GitHub Secrets, never in code
- **Risk**: pg_dump fails silently → **Mitigation**: Script validates output file size > 0

## Security Considerations
- Database URL stored in GitHub Secrets (encrypted at rest)
- Backup files in GitHub Artifacts (private repo access only)
- pg_dump uses SSL connection to Supabase
- Never commit database credentials to repository

## Next Steps
- Phase 3: Document and test restore procedures
