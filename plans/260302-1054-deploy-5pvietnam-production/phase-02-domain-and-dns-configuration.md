# Phase 2: Domain & DNS Configuration

## Context Links
- [Research: Hosting Platforms - DNS Section](research/researcher-01-hosting-platforms.md)
- [Phase 1: Platform Setup](phase-01-platform-setup-railway-and-vercel.md)

## Overview
- **Priority**: P1 (blocks frontend-backend connectivity)
- **Status**: pending
- **Effort**: 30 min
- **Description**: Configure 5pvietnam.com DNS to point frontend to Vercel, backend API to Railway, with SSL auto-provisioning

## Key Insights
- Vercel provides automatic SSL for custom domains
- Railway provides automatic SSL for custom domains
- DNS propagation typically <30 min but can take up to 48h
- Use CNAME records for both services (no static IPs needed)

## Requirements

### Functional
- `5pvietnam.com` and `www.5pvietnam.com` serve the React frontend
- `api.5pvietnam.com` serves the FastAPI backend
- HTTPS works on all domains (auto-SSL)

### Non-Functional
- DNS propagation < 1h (use low TTL initially)
- No downtime during DNS switch

## Architecture

```
DNS Records (5pvietnam.com registrar):

  @  (apex)     → Vercel (A records: 76.76.21.21)
  www           → CNAME → cname.vercel-dns.com
  api           → CNAME → <railway-app>.up.railway.app

SSL:
  5pvietnam.com       → Vercel auto-SSL (Let's Encrypt)
  www.5pvietnam.com   → Vercel auto-SSL
  api.5pvietnam.com   → Railway auto-SSL
```

## Related Code Files
- `frontend/vercel.json` - SPA routing (already configured)
- `backend/app/core/config.py` - ALLOWED_ORIGINS must include production domain

## Implementation Steps

### 1. Get Target Hostnames
1. From Railway dashboard: copy the service URL (e.g., `your-app.up.railway.app`)
2. From Vercel dashboard: note the project URL (e.g., `your-app.vercel.app`)

### 2. Configure DNS at Domain Registrar
Log into the registrar for `5pvietnam.com` and add these records:

| Type | Name | Value | TTL |
|------|------|-------|-----|
| A | @ | `76.76.21.21` | 300 |
| CNAME | www | `cname.vercel-dns.com` | 300 |
| CNAME | api | `<your-railway-app>.up.railway.app` | 300 |

**Note**: Vercel's A record IP `76.76.21.21` is their standard anycast IP. Verify current value in Vercel docs.

### 3. Add Custom Domain in Vercel
1. Vercel Dashboard > Project > Settings > Domains
2. Add `5pvietnam.com` (apex domain)
3. Add `www.5pvietnam.com` (redirect to apex or vice versa)
4. Vercel auto-provisions SSL certificate
5. Wait for "Valid Configuration" status

### 4. Add Custom Domain in Railway
1. Railway Dashboard > Service > Settings > Networking > Custom Domain
2. Add `api.5pvietnam.com`
3. Railway shows required CNAME target; verify it matches your DNS record
4. Railway auto-provisions SSL certificate
5. Wait for "Active" status

### 5. Verify DNS Propagation
```bash
# Check DNS resolution
dig 5pvietnam.com +short
dig www.5pvietnam.com +short
dig api.5pvietnam.com +short

# Check HTTPS
curl -I https://5pvietnam.com
curl -I https://api.5pvietnam.com
```

### 6. Update ALLOWED_ORIGINS
Ensure Railway env var `ALLOWED_ORIGINS` includes:
```
https://5pvietnam.com,https://www.5pvietnam.com
```
This should already be set in Phase 1.

## Todo List
- [ ] Get Railway service hostname
- [ ] Get Vercel project hostname
- [ ] Add A record for apex domain → Vercel
- [ ] Add CNAME `www` → Vercel
- [ ] Add CNAME `api` → Railway
- [ ] Add custom domain in Vercel dashboard
- [ ] Add custom domain in Railway dashboard
- [ ] Verify SSL auto-provisioning on all 3 domains
- [ ] Test `https://5pvietnam.com` loads frontend
- [ ] Test `https://api.5pvietnam.com/` returns API JSON
- [ ] Test `https://api.5pvietnam.com/docs` loads Swagger

## Success Criteria
- `https://5pvietnam.com` loads React app
- `https://www.5pvietnam.com` redirects to or loads React app
- `https://api.5pvietnam.com/` returns `{"message": "SLMS Backend API"}`
- All three domains have valid SSL certificates
- Frontend can make API calls to `api.5pvietnam.com` without CORS errors

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| DNS propagation slow (>1h) | Medium | Low | Set TTL=300; use DNS checker tools |
| SSL provisioning fails | Low | Medium | Verify DNS records correct; Railway/Vercel retry automatically |
| Apex domain A record conflicts | Low | Medium | Remove any existing A records before adding Vercel's |

## Security Considerations
- HTTPS enforced on all domains (HTTP auto-redirects to HTTPS)
- No wildcard DNS records (only explicit subdomains)
- Consider enabling DNSSEC at registrar level if supported

## Next Steps
- Once DNS is live: test frontend-to-backend API calls
- Proceed to Phase 3 (Backend Hardening) for security middleware
