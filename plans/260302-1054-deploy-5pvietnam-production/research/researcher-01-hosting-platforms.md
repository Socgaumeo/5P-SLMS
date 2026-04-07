# Hosting Platform Research: FastAPI + React/Vite Deployment (2026)

**Research Date**: 2026-03-02
**Database**: Supabase PostgreSQL (Singapore ap-southeast-1)
**Target**: Low-cost, simple deployment with Asia-Pacific optimization

---

## 1. Backend Hosting (FastAPI) Comparison

### Fly.io ⭐ RECOMMENDED for Asia-Pacific
- **Regions**: 35+ edge locations globally, **confirmed Singapore presence**
- **Latency**: 20-50ms API response in Singapore
- **Python 3.12**: Supported via Docker containers
- **Free Tier**: 3 shared-cpu-1x VMs (256MB RAM each), 3GB storage
- **Paid**: Usage-based, ~$5-15/month for small app (1 VM, 512MB RAM)
- **GitHub CI/CD**: Yes, auto-deploy from Git
- **SSL**: Auto Let's Encrypt
- **Pros**: Best latency for Asia, global edge network, colocated with Supabase
- **Cons**: Usage-based pricing requires monitoring

### Railway
- **Regions**: Americas, Europe, Asia-Pacific (specific cities unclear)
- **Latency**: 200-300ms from Singapore to US/EU regions
- **Python 3.12**: Supported
- **Free Tier**: $5 monthly credit (hobby plan)
- **Paid**: Usage-based, ~$10-20/month for small app
- **GitHub CI/CD**: Yes, seamless Git integration
- **SSL**: Auto
- **Pros**: Fast provisioning, managed DBs available, good DX
- **Cons**: Poor Asia-Pacific latency, usage caps, credit system

### Render
- **Regions**: Oregon, Frankfurt, Singapore (limited)
- **Latency**: Good if Singapore region available
- **Python 3.12**: Supported, ASGI/Uvicorn optimized
- **Free Tier**: Yes (spins down after inactivity)
- **Paid**: Flat $7/month (starter), $25/month (standard)
- **GitHub CI/CD**: Yes, auto-deploy
- **SSL**: Auto Let's Encrypt
- **Pros**: Predictable pricing, managed services, FastAPI-optimized
- **Cons**: Fewer global regions vs Fly.io, free tier sleeps

### DigitalOcean App Platform
- **Regions**: SGP1 (Singapore) available
- **Latency**: Excellent in Asia
- **Python 3.12**: Supported
- **Free Tier**: None
- **Paid**: $5/month (basic), $12/month (pro)
- **GitHub CI/CD**: Yes
- **SSL**: Auto
- **Pros**: Predictable pricing, Singapore region, managed DBs
- **Cons**: No free tier, less edge optimization vs Fly.io

### AWS Lightsail
- **Regions**: Singapore ap-southeast-1
- **Latency**: Good in Asia
- **Python 3.12**: Manual setup required
- **Free Tier**: 3 months (limited)
- **Paid**: $5/month (1 vCPU, 512MB RAM, 1TB transfer)
- **GitHub CI/CD**: Manual setup
- **SSL**: Manual Let's Encrypt or AWS Certificate Manager
- **Pros**: AWS ecosystem, predictable pricing
- **Cons**: More complex setup, manual SSL/CI/CD

### VPS: Hetzner vs DigitalOcean Droplet
**Hetzner**:
- **Regions**: 1 Singapore datacenter
- **Paid**: From $4.09/month (cloud), $42/month (dedicated)
- **Pros**: Cheapest option, full control
- **Cons**: Manual setup (Docker, Nginx, SSL, CI/CD), no managed services

**DigitalOcean Droplet**:
- **Regions**: Singapore available
- **Paid**: $4/month (basic), $6/month (regular)
- **Pros**: Good global coverage, better docs than Hetzner
- **Cons**: Manual setup, no managed DB/K8s on cheapest tier

---

## 2. Frontend CDN Deployment (React/Vite)

### Cloudflare Pages ⭐ RECOMMENDED
- **CDN**: 300+ global nodes, largest edge network
- **Bandwidth**: **Unlimited** on all plans
- **Free Tier**: 500 builds/month, unlimited bandwidth, custom domain
- **Paid**: $20/month (Pro, rarely needed for small apps)
- **Custom Domain**: Yes, auto-SSL
- **GitHub CI/CD**: Yes
- **Pros**: Best value, unlimited bandwidth, fastest CDN, free tier generous
- **Cons**: Steeper learning curve vs Vercel/Netlify

### Vercel
- **CDN**: Global edge network
- **Bandwidth**: 100GB/month (free), unlimited (Pro)
- **Free Tier**: Hobby plan, 100k serverless invocations
- **Paid**: $20/user/month (Pro)
- **Custom Domain**: Yes, auto-SSL
- **GitHub CI/CD**: Best-in-class
- **Pros**: Best DX, Next.js optimization, instant previews
- **Cons**: Expensive at scale, usage-based overage costs

### Netlify
- **CDN**: Global edge network
- **Bandwidth**: 100GB/month (free)
- **Free Tier**: 300 build minutes/month
- **Paid**: $19-50/month (Pro, usage-based)
- **Custom Domain**: Yes, auto-SSL
- **GitHub CI/CD**: Yes
- **Pros**: Framework-agnostic, good balance of features
- **Cons**: Similar limits to Vercel, usage-based pricing

---

## 3. DNS Configuration (5pvietnam.com)

### Setup Steps:
1. **Choose DNS management**:
   - Option A: Delegate nameservers to hosting provider (recommended)
   - Option B: Add A/CNAME records pointing to hosting provider

2. **Typical Records**:
   - **A Record**: `@` → hosting IP (for apex domain)
   - **CNAME Record**: `www` → hosting URL
   - **Backend subdomain**: `api.5pvietnam.com` → backend hosting

3. **Propagation**: 15 minutes - 48 hours (typically <30 min)

---

## 4. SSL/HTTPS

All modern platforms provide **auto-SSL via Let's Encrypt**:
- **Fly.io, Railway, Render, DigitalOcean App Platform**: Auto-SSL on custom domains
- **Cloudflare Pages, Vercel, Netlify**: Auto-SSL included
- **Manual (VPS)**: Certbot + Let's Encrypt (free, requires cron renewal)

### DNS Challenge:
Required for wildcard certs: TXT record `_acme-challenge.<domain>` for validation.

---

## 5. Cost Estimation (100 users/day, low traffic)

### Recommended Stack (Asia-Optimized):
| Component | Service | Monthly Cost |
|-----------|---------|--------------|
| Backend (FastAPI) | **Fly.io** (1 VM, 512MB) | $5-10 |
| Frontend (React/Vite) | **Cloudflare Pages** (free tier) | $0 |
| Database | **Supabase** (Singapore, free tier) | $0 |
| Domain | 5pvietnam.com | ~$12/year |
| **Total** | | **$5-10/month** |

### Alternative Stacks:

**Budget Option (Manual Setup)**:
- Hetzner VPS ($4.09/month) + Cloudflare Pages ($0) = **$4/month**
- Requires Docker, Nginx, SSL, CI/CD manual setup

**Simplicity Option**:
- DigitalOcean App Platform ($5 backend + $0 frontend) = **$5/month**
- Render ($7 backend + Cloudflare Pages $0) = **$7/month**

**Premium Option**:
- Railway ($10-20) + Vercel ($20) = **$30-40/month** (overkill for 100 users/day)

---

## 6. Final Recommendations

### For Your Requirements (Asia-Pacific, Low Cost, Simple):

**🥇 Best Overall**: Fly.io (backend) + Cloudflare Pages (frontend)
- ✅ Singapore edge presence (20-50ms latency)
- ✅ Auto-deploy from GitHub
- ✅ Auto-SSL
- ✅ ~$5-10/month total cost
- ✅ Scales easily if traffic grows
- ⚠️ Usage-based pricing (monitor costs)

**🥈 Simplest Setup**: Render (backend) + Cloudflare Pages (frontend)
- ✅ Predictable flat pricing ($7/month)
- ✅ FastAPI-optimized
- ✅ Auto-deploy, auto-SSL
- ⚠️ Free tier spins down (upgrade to $7 starter)
- ⚠️ Check Singapore region availability

**🥉 Budget Champion**: Hetzner VPS ($4) + Cloudflare Pages ($0)
- ✅ Cheapest option
- ✅ Full control
- ❌ Manual setup complexity (not beginner-friendly)

---

## Unresolved Questions

1. Does Render currently support Singapore region deployment in 2026?
2. What is exact Supabase connection pooling limit on free tier?
3. Does 5pvietnam.com need DNSSEC configuration?
4. Expected traffic growth timeline (impacts scaling needs)?

---

## Sources

- [DigitalOcean: Render Alternatives](https://www.digitalocean.com/resources/articles/render-alternatives)
- [Python Hosting Comparison 2025](https://www.nandann.com/blog/python-hosting-options-comparison)
- [Northflank: Render Alternatives](https://northflank.com/blog/render-alternatives)
- [Vercel vs Netlify vs Cloudflare 2025](https://www.digitalapplied.com/blog/vercel-vs-netlify-vs-cloudflare-pages-comparison)
- [Cloudflare Pages Deployment Guide](https://eastondev.com/blog/en/posts/dev/20251201-cloudflare-pages-deploy-guide/)
- [Fly.io Pricing](https://fly.io/pricing/)
- [AWS Lightsail Pricing](https://aws.amazon.com/lightsail/pricing/)
- [DigitalOcean vs Hetzner](https://www.digitalocean.com/resources/articles/digitalocean-vs-hetzner)
- [FastAPI on VPS Deployment](https://turbocloud.dev/book/deploy-fastapi/)
- [Railway Regions Documentation](https://docs.railway.com/deployments/regions)
- [Fly.io vs Railway Comparison](https://thesoftwarescout.com/fly-io-vs-railway-2026-which-developer-platform-should-you-deploy-on/)
- [Supabase Performance Tuning](https://supabase.com/docs/guides/platform/performance)
- [Custom Domain SSL on DigitalOcean](https://www.digitalocean.com/community/tutorials/how-to-configure-custom-domains-ssl-cdn)
