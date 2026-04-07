# Phase 04: DNS, SSL & Domain Setup

## Context Links

- [plan.md](plan.md) - Overview
- [phase-02](phase-02-deploy-frontend-to-vercel.md) - Vercel domain config
- [phase-03](phase-03-deploy-backend-to-railway.md) - Railway domain config

## Overview

- **Priority**: P1
- **Status**: pending
- **Effort**: 30m
- **Description**: Configure DNS records to point 5pvietnam.com to Vercel and api.5pvietnam.com to Railway. Verify SSL auto-provisioning.

## Key Insights

- Cloudflare recommended as DNS provider (free CDN, DDoS protection, analytics)
- If domain is at another registrar, can either transfer nameservers to Cloudflare or add records at registrar
- Both Vercel and Railway auto-provision Let's Encrypt SSL certificates
- SSL provisioning takes 5-15 minutes after DNS propagation
- DNS propagation: typically 5-30min, worst case 48h (TTL dependent)

## Requirements

### Functional
- `https://5pvietnam.com` resolves to Vercel (frontend)
- `https://www.5pvietnam.com` redirects to `https://5pvietnam.com`
- `https://api.5pvietnam.com` resolves to Railway (backend)
- All HTTP requests redirect to HTTPS

### Non-Functional
- DNS propagation < 30min
- SSL certificates valid and auto-renewing
- No mixed content warnings

## Architecture

```
Domain Registrar (5pvietnam.com)
├── Option A: Point nameservers to Cloudflare
│   └── Cloudflare manages all DNS records
└── Option B: Add records directly at registrar

DNS Records:
┌────────────────────────────────────────────────────┐
│ Type  │ Name              │ Value                  │
├───────┼───────────────────┼────────────────────────┤
│ A     │ 5pvietnam.com     │ 76.76.21.21 (Vercel)   │
│ CNAME │ www               │ cname.vercel-dns.com   │
│ CNAME │ api               │ <service>.up.railway.app│
└────────────────────────────────────────────────────┘
```

## Related Code Files

No code changes in this phase. Pure infrastructure configuration.

## Implementation Steps

### 1. Get Target Values from Vercel & Railway

**From Vercel** (after Phase 02):
1. Go to Project > Settings > Domains
2. Add `5pvietnam.com` - Vercel shows required DNS records
3. Typically: A record → `76.76.21.21` or CNAME → `cname.vercel-dns.com`

**From Railway** (after Phase 03):
1. Go to Service > Settings > Custom Domain
2. Add `api.5pvietnam.com`
3. Railway shows CNAME target (e.g., `<service-hash>.up.railway.app`)

### 2. Option A: Setup Cloudflare (Recommended)

1. Create free Cloudflare account at [dash.cloudflare.com](https://dash.cloudflare.com)
2. Add site `5pvietnam.com`
3. Cloudflare provides 2 nameservers (e.g., `ana.ns.cloudflare.com`, `bob.ns.cloudflare.com`)
4. At domain registrar, change nameservers to Cloudflare's
5. Wait for nameserver propagation (up to 24h, usually < 1h)

**Add DNS records in Cloudflare:**

| Type | Name | Content | Proxy |
|------|------|---------|-------|
| A | `@` | `76.76.21.21` | DNS Only (grey cloud) |
| CNAME | `www` | `cname.vercel-dns.com` | DNS Only (grey cloud) |
| CNAME | `api` | `<service>.up.railway.app` | DNS Only (grey cloud) |

**IMPORTANT**: Set Proxy to "DNS Only" (grey cloud icon) for all records. Vercel and Railway handle SSL themselves; Cloudflare proxy would conflict with their SSL provisioning.

### 2b. Option B: Records at Domain Registrar

If not using Cloudflare, add the same records directly at the registrar's DNS panel. Same records, just no CDN/DDoS protection.

### 3. Verify DNS Propagation

```bash
# Check A record for apex domain
dig 5pvietnam.com +short
# Expected: 76.76.21.21

# Check CNAME for www
dig www.5pvietnam.com +short
# Expected: cname.vercel-dns.com

# Check CNAME for api
dig api.5pvietnam.com +short
# Expected: <service>.up.railway.app

# Alternative: use online tool
# https://dnschecker.org/#A/5pvietnam.com
```

### 4. Verify SSL Certificates

After DNS propagates (5-15 min):

```bash
# Check Vercel SSL
curl -I https://5pvietnam.com
# Look for: HTTP/2 200, strict-transport-security header

# Check Railway SSL
curl -I https://api.5pvietnam.com/health
# Look for: HTTP/2 200, valid SSL
```

Both platforms auto-provision Let's Encrypt certificates. If SSL fails:
- Verify DNS is pointing correctly (step 3)
- Wait longer (can take up to 1h)
- Check platform dashboards for SSL status/errors

### 5. Verify HTTPS Redirect

```bash
# HTTP should redirect to HTTPS
curl -I http://5pvietnam.com
# Expected: 301/308 redirect to https://5pvietnam.com

curl -I http://api.5pvietnam.com
# Expected: 301/308 redirect to https://api.5pvietnam.com
```

### 6. Optional: Enable Cloudflare Features

If using Cloudflare, consider enabling later:
- **Always Use HTTPS**: SSL/TLS > Edge Certificates > toggle on
- **HSTS**: SSL/TLS > Edge Certificates > enable (only after confirming everything works)
- **Analytics**: Free traffic analytics
- **Page Rules**: Cache static assets

**Do NOT enable** until everything is verified working:
- Cloudflare Proxy (orange cloud) - conflicts with Vercel/Railway SSL
- Rocket Loader - can break React SPA
- Minification - Vite already handles this

## Todo List

- [ ] Get Vercel DNS target values (A/CNAME records)
- [ ] Get Railway CNAME target for api subdomain
- [ ] Choose DNS approach: Cloudflare (recommended) vs registrar
- [ ] If Cloudflare: create account, add site, update nameservers
- [ ] Add A record for `5pvietnam.com` → Vercel
- [ ] Add CNAME for `www` → Vercel
- [ ] Add CNAME for `api` → Railway
- [ ] Verify DNS propagation with `dig` commands
- [ ] Verify SSL auto-provisioned on both domains
- [ ] Verify HTTPS redirect works
- [ ] Test full flow: load site, login, API calls work

## Success Criteria

- `dig 5pvietnam.com` returns Vercel IP
- `dig api.5pvietnam.com` returns Railway CNAME
- `https://5pvietnam.com` loads React app with valid SSL
- `https://api.5pvietnam.com/health` returns healthy with valid SSL
- `http://` redirects to `https://` on both domains
- No browser SSL warnings

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Slow DNS propagation | Medium | Low | Wait 48h max; check dnschecker.org |
| SSL provisioning fails | Low | High | Verify DNS is correct; check platform status pages |
| Cloudflare proxy conflicts | Medium | High | Use "DNS Only" mode (grey cloud) |
| Wrong DNS records | Medium | High | Double-check values from Vercel/Railway dashboards |

## Security Considerations

- HTTPS enforced on all endpoints
- HSTS headers added by Vercel/Railway
- Cloudflare provides DDoS protection even in DNS-only mode (at nameserver level)
- No wildcard DNS records (only specific subdomains)

## Next Steps

- Phase 05: CI/CD pipeline (auto-deploy on push)
- Full E2E testing after DNS is live
