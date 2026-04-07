# Phase 00: Remove Hardcoded Secrets from Codebase

## Context Links
- Parent: [plan.md](plan.md)
- File: `backend/app/core/config.py`

## Overview
- **Priority**: CRITICAL
- **Status**: pending
- **Description**: Remove hardcoded DATABASE_URL (with real password) from config.py. Repo is PUBLIC - credentials are exposed.

## Key Insights
- `config.py:14` has hardcoded DATABASE_URL with actual Supabase password
- `config.py:39` has placeholder SECRET_KEY
- `config.py:42` has placeholder JWT_SECRET_KEY
- Repo is PUBLIC on GitHub - anyone can see these credentials

## Requirements
- All secrets must come from environment variables only
- Default values must be empty/placeholder (not real credentials)
- App must fail fast if required secrets missing in production

## Related Code Files
- **Modify**: `backend/app/core/config.py` - remove hardcoded defaults for secrets
- **Create**: `backend/.env.example` - template with empty values

## Implementation Steps
1. Remove hardcoded DATABASE_URL default from config.py (set to empty string)
2. Remove placeholder SECRET_KEY and JWT_SECRET_KEY defaults
3. Add validation: raise error if secrets missing when DEBUG=False
4. Create `.env.example` with all required env vars (empty values)
5. Verify `.env` is in `.gitignore`
6. Consider rotating Supabase password since it was exposed in public repo

## Todo List
- [ ] Remove hardcoded DATABASE_URL from config.py
- [ ] Remove hardcoded SECRET_KEY defaults
- [ ] Add production validation for required secrets
- [ ] Create .env.example
- [ ] Verify .gitignore includes .env
- [ ] Rotate exposed Supabase password

## Success Criteria
- No real credentials in any committed file
- App starts with .env file, fails without required vars in production

## Risk Assessment
- **HIGH**: Exposed database credentials in public repo
- **Mitigation**: Rotate Supabase password after removing from code

## Security Considerations
- Rotate all exposed credentials after cleanup
- Consider making repo private before deployment

## Next Steps
- After cleanup, proceed to Phase 01 (production configs)
