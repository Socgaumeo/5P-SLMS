# Deployment, CI/CD & Security Research Report
**Domain:** 5pvietnam.com | **Stack:** FastAPI + React/Vite + Supabase

## 1. DNS Configuration

### Vercel (Frontend)
- **Apex domain:** Add A record at DNS provider
- **Subdomain:** Add CNAME record
- **Wildcard domains** (*.5pvietnam.com): Must use Vercel nameservers (ns1.vercel-dns.com, ns2.vercel-dns.com) for SSL wildcard certificates
- DNS propagation: Takes time globally, some regions accessible before others

### Railway (Backend)
- Create CNAME record with Railway-provided value at DNS provider (Cloudflare/Namecheap/etc)
- **Apex/root domains:** Railway supports CNAME Flattening + dynamic ALIAS records
- With Cloudflare: Simply set CNAME for root domain, Cloudflare handles flattening
- Auto Let's Encrypt cert after verification, auto-renewed at 30 days validity

## 2. SSL/HTTPS Options

### Free SSL Solutions
**Cloudflare (Recommended)**
- Free plan auto-generates SSL cert when domain added
- Set SSL/TLS mode to "Full" or "Full (strict)"
- Cert auto-issued (Let's Encrypt or Google Trust Services)
- Over 250M domains use Let's Encrypt (2026)

**Let's Encrypt Manual Setup**
```bash
sudo apt install certbot python3-certbot-dns-cloudflare
# Use DNS challenge (HTTP validation won't work with Cloudflare proxy)
# Configure dns_cloudflare_api_token in certbot config
```

**Platform-Managed**
- **Railway:** Auto Let's Encrypt cert for custom domains
- **Vercel:** Auto SSL for all domains
- **Render:** Auto SSL with custom domains

### End-to-End Encryption
Cloudflare → Origin server: Use "Full (strict)" mode with valid cert on origin

## 3. CI/CD with GitHub Actions

### Frontend (React/Vite)
```yaml
name: Deploy Frontend
on:
  push:
    branches: [main]
    paths: ['frontend/**']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
        working-directory: frontend
      - run: npm run build
        working-directory: frontend
      - uses: vercel/action@v2
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
```

**Vite specifics:**
- Default build output: `dist/` directory
- Cache node_modules based on lockfile hash
- Cache Vite build artifacts for faster rebuilds

### Backend (FastAPI)
```yaml
name: Deploy Backend
on:
  push:
    branches: [main]
    paths: ['backend/**']
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest
  deploy:
    needs: test  # Only deploy if tests pass
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: railway up  # Or render deploy / docker push
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

**Key pattern:** `needs: test` prevents bad code reaching production

## 4. Environment Variables & Secrets

### GitHub Actions Secrets
Store in repo Settings → Secrets and variables → Actions:
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `DEEPSEEK_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_KEY`
- `VERCEL_TOKEN` / `RAILWAY_TOKEN`

### Backend .env (Production)
```bash
# FastAPI Config
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info

# CORS
ALLOWED_ORIGINS=https://5pvietnam.com,https://www.5pvietnam.com
ALLOWED_CREDENTIALS=True
ALLOWED_METHODS=*
ALLOWED_HEADERS=*

# API Keys (from platform env vars)
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
GEMINI_API_KEY=${GEMINI_API_KEY}
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}

# Supabase
SUPABASE_URL=${SUPABASE_URL}
SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
```

**Load with python-dotenv:**
```python
from dotenv import load_dotenv
load_dotenv()  # Loads from .env file
```

## 5. Security Hardening

### CORS Config (Production)
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://5pvietnam.com",
        "https://www.5pvietnam.com"
    ],  # NEVER use ["*"] in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600  # Cache preflight for 1 hour
)
```

### Rate Limiting
**With Upstash Redis:**
```python
# pip install fastapi-limiter redis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@app.on_event("startup")
async def startup():
    redis = await aioredis.from_url("redis://...", encoding="utf8")
    await FastAPILimiter.init(redis)

@app.get("/api/endpoint", dependencies=[Depends(RateLimiter(times=10, hours=1))])
```

**Default config:**
- 10 requests per hour per IP
- Use fixed window limiter for simplicity

### Gunicorn + Uvicorn Production Setup
```bash
# gunicorn_conf.py
bind = "0.0.0.0:8000"
workers = (2 * cpu_count) + 1  # e.g., 5 for 2-core
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
keepalive = 5
```

**Run:**
```bash
gunicorn -c gunicorn_conf.py app.main:app
```

### Security Headers (Nginx/Middleware)
```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)  # Force HTTPS
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["5pvietnam.com", "*.5pvietnam.com"])
```

**Additional headers (via Nginx or middleware):**
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy: default-src 'self'`

### Production Checklist
- [ ] CORS: Explicit origins only
- [ ] Rate limiting on all endpoints
- [ ] Environment vars via platform secrets (not .env in repo)
- [ ] HTTPS enforced
- [ ] Gunicorn worker count = (2*CPU)+1
- [ ] Security headers configured
- [ ] Tests pass before deployment
- [ ] Supabase RLS policies enabled

---

## Sources
- [FastAPI Deployment Guide 2026](https://www.zestminds.com/blog/fastapi-deployment-guide/)
- [FastAPI Production Deployment](https://oneuptime.com/blog/post/2026-02-02-fastapi-production-deployment/view)
- [GitHub Actions CI/CD React](https://oneuptime.com/blog/post/2026-01-15-cicd-pipelines-react-github-actions/view)
- [Vercel Custom Domains](https://vercel.com/docs/domains/working-with-domains/add-a-domain)
- [Railway Custom Domains](https://docs.railway.com/networking/domains/working-with-domains)
- [FastAPI Production Best Practices](https://render.com/articles/fastapi-production-deployment-best-practices)
- [Let's Encrypt Cloudflare SSL](https://medium.com/@pharmifedayoojo/getting-a-free-ssl-certificate-for-your-cloudflare-domain-with-lets-encrypt-38524655e859)
