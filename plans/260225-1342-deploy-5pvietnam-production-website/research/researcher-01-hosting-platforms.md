# Hosting Platform Research: FastAPI + React/Vite Deployment

**Date:** 2026-02-25
**Purpose:** Evaluate hosting options for 5pvietnam.com (FastAPI backend + React/Vite frontend)
**Database:** Supabase PostgreSQL (Singapore ap-southeast-1)
**Target Users:** ~100 users, low traffic, Vietnam-based

---

## Platform Comparison Table

| Platform | Frontend | Backend | Cost (mo) | Free Tier | SEA Latency | Ease of Setup | Best For |
|----------|----------|---------|-----------|-----------|-------------|---------------|----------|
| **Render** | ✅ | ✅ | $7+ | ❌ (14-day trial) | Good (global CDN) | ⭐⭐⭐⭐⭐ | Production-ready, integrated |
| **Railway** | ✅ | ✅ | $5+ | ❌ ($5 trial credit) | Good | ⭐⭐⭐⭐⭐ | Fast MVP iteration |
| **Vercel + Railway** | ✅ (free) | ✅ ($5) | $5 | ✅ Frontend only | Excellent (edge) | ⭐⭐⭐⭐ | Split deployment |
| **DigitalOcean App** | ✅ | ✅ | $12+ | ❌ ($200/60d credit) | Good (SGP datacenter) | ⭐⭐⭐⭐ | Production teams |
| **Fly.io** | ✅ | ✅ | $5-15+ | ✅ (3 VMs) | Excellent (multi-region) | ⭐⭐⭐ | Multi-region apps |
| **AWS Lightsail** | ✅ | ✅ | $3.50+ | ❌ | Excellent (ap-southeast-1) | ⭐⭐ | Full control, hidden costs |
| **AWS ECS/EC2** | ✅ | ✅ | $15+ | ✅ (12mo free tier) | Excellent (ap-southeast-1) | ⭐ | Enterprise, custom config |

---

## Detailed Analysis

### 1. **Render** [🔗](https://render.com)
- **Pros:** One-click Git deploy, flat pricing, ASGI (Uvicorn) support, integrated DB services
- **Cons:** No permanent free tier, starts $7/mo
- **SEA Latency:** Global CDN, ~40-60ms to Vietnam
- **Setup:** Connect GitHub → Auto-deploy
- **Cost:** Static site (free) + Web service ($7) = **$7/mo** for hobby

### 2. **Railway** [🔗](https://railway.com)
- **Pros:** Simplest setup, Docker support, FastAPI+React templates, $5/mo covers most hobby projects
- **Cons:** No permanent free tier (only $5 trial credit), can run out fast if 24/7
- **SEA Latency:** Good global routing, ~50ms to Vietnam
- **Setup:** GitHub connect → Deploy in minutes
- **Cost:** $5/mo Hobby plan after trial = **$5/mo**

### 3. **Vercel (Frontend) + Railway (Backend)** [🔗](https://vercel.com) [🔗](https://railway.com)
- **Pros:** Vercel free tier for React/Vite, Railway $5/mo for FastAPI, specialized platforms
- **Cons:** Split deployments, CORS config needed
- **SEA Latency:** Vercel edge ~20-30ms, Railway backend ~50ms
- **Setup:** Vercel auto-deploy frontend, Railway for backend
- **Cost:** Vercel (free) + Railway ($5) = **$5/mo** total

### 4. **DigitalOcean App Platform** [🔗](https://digitalocean.com)
- **Pros:** Singapore datacenter (ap-southeast-1), production-ready, autoscaling
- **Cons:** Higher cost, no permanent free tier
- **SEA Latency:** Excellent (~10-20ms from Singapore to Vietnam)
- **Setup:** GitHub-based, detailed logs/metrics
- **Cost:** Basic Web Service ($12) = **$12/mo**

### 5. **Fly.io** [🔗](https://fly.io)
- **Pros:** Free tier (3 shared VMs + 160GB bandwidth), multi-region, edge computing
- **Cons:** Usage-based pricing can spike, egress costs ($0.02/GB), complex for beginners
- **SEA Latency:** Excellent (can deploy to Singapore region), <30ms
- **Setup:** Moderate complexity, CLI-based
- **Cost:** Free tier → $5-15/mo with bandwidth/storage = **$5-15/mo**

### 6. **AWS Lightsail** [🔗](https://aws.amazon.com/lightsail)
- **Pros:** Singapore region (ap-southeast-1), cheap entry ($3.50), 1TB transfer
- **Cons:** Hidden costs (snapshots $0.05/GB, overage $0.09/GB), manual setup
- **SEA Latency:** Excellent (~10-20ms)
- **Setup:** Manual (SSH, Docker, Nginx reverse proxy)
- **Cost:** $3.50-5 instance + snapshots/overage = **$10-20/mo** real cost

### 7. **AWS ECS/EC2** [🔗](https://aws.amazon.com/ecs)
- **Pros:** Enterprise-grade, Singapore region, 12-month free tier (t2.micro)
- **Cons:** Complex setup, DevOps knowledge required, cost creep after free tier
- **SEA Latency:** Excellent (~10-20ms)
- **Setup:** High complexity (VPC, ALB, ECS tasks, CloudWatch)
- **Cost:** Free tier (12mo) → $15-30/mo after = **$0-30/mo**

---

## Vietnam/SEA Latency Rankings

1. **DigitalOcean (Singapore)** - 10-20ms ⭐⭐⭐⭐⭐
2. **AWS ap-southeast-1** - 10-20ms ⭐⭐⭐⭐⭐
3. **Fly.io (Singapore region)** - 20-30ms ⭐⭐⭐⭐
4. **Vercel Edge** - 20-30ms ⭐⭐⭐⭐
5. **Railway** - 40-50ms ⭐⭐⭐
6. **Render** - 40-60ms ⭐⭐⭐

Since DB already in Singapore (Supabase), hosting backend in Singapore minimizes DB latency (<5ms).

---

## Cost Estimation (100 users, low traffic)

| Platform | Monthly Cost | Annual Cost |
|----------|--------------|-------------|
| Vercel + Railway | $5 | $60 |
| Railway | $5 | $60 |
| Render | $7 | $84 |
| Fly.io | $5-15 | $60-180 |
| AWS Lightsail | $10-20 | $120-240 |
| DigitalOcean | $12 | $144 |
| AWS ECS | $0-30 (free tier → paid) | $0-360 |

---

## Recommendation

### **Best Option: Vercel (Frontend) + Railway (Backend)**
**Cost:** $5/mo | **Latency:** Excellent | **Setup:** Easy

**Rationale:**
- **Free Vercel frontend** (generous free tier, edge network, 20-30ms Vietnam latency)
- **Railway backend $5/mo** (simplest FastAPI deployment, Docker support, Git auto-deploy)
- **Total cost:** $5/mo (cheapest production option)
- **Supabase Singapore:** Backend on Railway can be Singapore region → <5ms DB latency
- **Ease:** Both platforms have 1-click GitHub deploy, zero DevOps
- **Scalability:** Easy upgrade path (Railway Pro $20/mo, Vercel Pro $20/mo)

### **Alternative: Railway Full Stack**
**Cost:** $5/mo | **Setup:** Simplest

If prefer single platform, Railway alone for both frontend+backend works well, uses same $5/mo Hobby plan.

### **For Production Scale (>1000 users):**
- **DigitalOcean App Platform** ($12/mo) - Singapore datacenter, best latency
- **AWS ECS** - Enterprise control, but complex

---

## Setup Steps (Recommended: Vercel + Railway)

### Frontend (Vercel):
1. Push React/Vite to GitHub
2. Import to Vercel → Auto-detect Vite
3. Set env vars (API_URL → Railway backend URL)
4. Deploy → Live on Vercel edge network

### Backend (Railway):
1. Push FastAPI to GitHub
2. Import to Railway → Detect Dockerfile
3. Set env vars (SUPABASE_URL, SUPABASE_KEY, DATABASE_URL)
4. Deploy → Get Railway URL (https://xxx.up.railway.app)

### Domain (5pvietnam.com):
1. Vercel: Add custom domain → Get DNS records
2. Update DNS: Point 5pvietnam.com to Vercel, api.5pvietnam.com to Railway
3. SSL auto-provisioned by both platforms

---

## Unresolved Questions

1. **Traffic patterns:** Expected requests/day? (affects bandwidth costs on Fly.io/Lightsail)
2. **Growth timeline:** When expect 100 → 1000 users? (impacts platform choice)
3. **CI/CD needs:** GitHub Actions, testing pipeline requirements?
4. **Monitoring:** Need APM (Sentry, DataDog) or built-in metrics sufficient?
5. **Budget ceiling:** Max acceptable monthly hosting cost?

---

## Sources

- [Railway FastAPI Guide](https://docs.railway.com/guides/fastapi)
- [Render Alternatives 2026](https://northflank.com/blog/render-alternatives)
- [Python Hosting Comparison 2025](https://www.nandann.com/blog/python-hosting-options-comparison)
- [Railway vs Render 2026](https://northflank.com/blog/railway-vs-render)
- [Fly.io Pricing](https://fly.io/pricing/)
- [AWS Lightsail Cost Comparison](https://massivegrid.com/blog/aws-lightsail-vs-traditional-vps-cost-comparison/)
- [Singapore Low-Latency VPS](https://massivegrid.com/blog/low-latency-vps-asia-pacific-singapore/)
- [Vercel FastAPI Backend](https://vercel.com/docs/frameworks/backend/fastapi)
- [Railway vs Vercel](https://docs.railway.com/platform/compare-to-vercel)
- [FastAPI Production Best Practices 2026](https://fastlaunchapi.dev/blog/fastapi-best-practices-production-2026)
- [Top FastAPI Hosting Providers](https://blog.back4app.com/fastapi-hosting-providers/)
