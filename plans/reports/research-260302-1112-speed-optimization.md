# Speed Optimization Research Report
**Date:** 2026-03-02
**Target:** FastAPI (Railway) + React/Vite (Vercel) + Supabase (Singapore)
**Budget:** <$10/month

---

## 1. Vercel Speed Insights (React + Vite)

### Correct Setup (NOT Next.js)
```bash
npm i @vercel/speed-insights
```

```javascript
// App.jsx or main.jsx
import { SpeedInsights } from '@vercel/speed-insights/react'

function App() {
  return (
    <>
      <YourApp />
      <SpeedInsights />
    </>
  )
}
```

**Key Points:**
- Use `@vercel/speed-insights/react` (NOT `/next`)
- Deploy to Vercel to view insights
- Free for all Vercel deployments

**Sources:** [Vercel Docs](https://vercel.com/docs/speed-insights/quickstart), [Medium Guide](https://medium.com/@dilhanziriwardhana/how-to-add-vercel-speed-insights-in-react-8df0a9bdf075)

---

## 2. Frontend Performance (React + Vite)

### A. Vite Build Optimization
```javascript
// vite.config.js
export default {
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['@mui/material', 'other-ui-libs']
        }
      }
    },
    chunkSizeWarningLimit: 500,
    minify: 'esbuild' // or 'oxc' for Vite 8+
  }
}
```

**Key Strategies:**
- **Manual chunks:** Vendor split reduces main bundle 40-60%
- **Minifier:** Vite 6+ uses Rolldown (Rust), 70% faster builds
- **Tree shaking:** Automatic via ES modules

**Sources:** [Vite Docs](https://vite.dev/config/build-options), [Optimization Guide](https://dev.to/perisicnikola37/optimize-vite-build-time-a-comprehensive-guide-4c99)

### B. React Lazy Loading
```javascript
import { lazy, Suspense } from 'react'

const Dashboard = lazy(() => import('./Dashboard'))

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Dashboard />
    </Suspense>
  )
}
```

**Benefits:**
- 40% initial JS reduction
- Route-based splitting via React Router
- Dynamic imports create separate chunks

**Sources:** [Medium Guide](https://benmukebo.medium.com/boost-your-react-apps-performance-with-vite-lazy-loading-and-code-splitting-2fd093128682), [DEV Community](https://dev.to/sperez927/slice-your-js-lazy-load-components-with-react-vite-dynamic-imports-mp8)

### C. Vercel Caching
```javascript
// vercel.json
{
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

**Auto-caching:**
- Static files: 31 days at edge (auto-hashed)
- Dynamic content: Use `Cache-Control` headers
- Cache invalidation: Auto on new deploy

**Sources:** [Vercel CDN](https://vercel.com/docs/edge-network/caching), [Medium Article](https://medium.com/@codfish/adding-cache-control-headers-for-static-assets-with-now-2-0-cb2664d8c3e9)

---

## 3. Backend Performance (FastAPI + Railway)

### A. Railway Latency (Asia)
- **Current:** Singapore region available
- **Latency:** ~150-200ms from Japan/Korea to Singapore
- **Optimization:** Multi-region replicas (automatic routing)
- **Read replicas:** Deploy in additional regions (writes still go to primary)

**Note:** Railway edge proxies route to nearest region automatically.

**Sources:** [Railway Docs](https://docs.railway.com/deployments/regions), [Performance Guide](https://docs.railway.com/deployments/optimize-performance)

### B. FastAPI Async Optimization
```python
# Proper async setup
from fastapi import FastAPI
from databases import Database

app = FastAPI()
database = Database("postgresql+asyncpg://...")

@app.on_event("startup")
async def startup():
    await database.connect()

# Use async endpoints
@app.get("/items")
async def get_items():
    return await database.fetch_all("SELECT * FROM items")
```

**Key Rules:**
- **async def + await:** Non-blocking I/O only
- **Worker count:** = CPU cores (not 2×cores+1 for async)
- **Never:** Blocking code in async endpoints
- **Pooling:** pool_size=10, max_overflow=20

**Uvicorn config:**
```bash
uvicorn main:app --workers 4 --loop uvloop
```

**Performance:** 10K req/s possible with Redis rate limiting

**Sources:** [FastAPI Guide](https://fastlaunchapi.dev/blog/fastapi-best-practices-production-2026), [Render Blog](https://render.com/articles/fastapi-production-deployment-best-practices)

### C. Supabase Connection Pooling
```python
# Use pooler connection string
DATABASE_URL = "postgresql://user:pass@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
```

**Configuration:**
- **Mode:** Transaction (mandatory for scalability)
- **Pool size:** 40% of max connections (if using PostgREST), 80% otherwise
- **Pooler:** Supavisor (PgBouncer replacement)
- **default_pool_size:** Connections per user/database
- **max_client_conn:** Max client connections

**Important:** Transaction mode doesn't support prepared statements

**Sources:** [Supabase Docs](https://supabase.com/docs/guides/database/connection-management), [FastAPI Guide](https://medium.com/@papansarkar101/supabase-connection-scaling-the-essential-guide-for-fastapi-developers-2dc5c428b638)

### D. Response Compression
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

---

## 4. Network Optimization (CDN + Proxy)

### A. Cloudflare Free Tier (Recommended)
**Setup:**
1. Add domain to Cloudflare
2. Point CNAME to Railway backend
3. Enable proxy (orange cloud)

**Benefits:**
- Global CDN (330+ PoPs)
- DDoS protection
- SSL/TLS
- Edge caching
- **Cost:** $0

**Architecture:**
```
User → Cloudflare Edge → Railway Proxy → FastAPI
```

**Sources:** [Railway vs Cloudflare](https://blog.railway.com/p/railway-vs-cloudflare-how-their-architectures-differ-and-when-to-use-each), [Setup Guide](https://community.cloudflare.com/t/setting-up-cloudflare-for-reverse-proxy/271509)

### B. Alternative: Bunny.net
- **Cost:** $0.01/GB (NA/EU)
- **Savings:** 70-85% vs Fastly
- **Best for:** Tight budgets

**Sources:** [CDN Alternatives](https://www.ioriver.io/blog/cloudflare-cdn-alternatives), [Comparison](https://postsnippets.com/best-cloudflare-alternatives/)

---

## 5. Cost Breakdown (<$10/month Target)

| Service | Tier | Cost |
|---------|------|------|
| Railway | Starter ($5) | $5 |
| Vercel | Hobby | $0 |
| Supabase | Free | $0 |
| Cloudflare | Free | $0 |
| **Total** | | **$5/mo** |

**Notes:**
- Railway free tier: $5 credit/month (may not suffice for production)
- Vercel bandwidth limits: 100GB/month (free tier)
- Supabase limits: 500MB database, 2GB bandwidth

---

## 6. Implementation Checklist

### Frontend (Vercel)
- [ ] Install `@vercel/speed-insights/react`
- [ ] Configure Vite manual chunks (vendor split)
- [ ] Implement React.lazy for routes
- [ ] Add Cache-Control headers in vercel.json
- [ ] Optimize images (WebP, lazy loading)

### Backend (Railway)
- [ ] Set up Cloudflare proxy
- [ ] Configure Uvicorn workers (count = CPU cores)
- [ ] Use Supabase pooler connection string
- [ ] Add GZip middleware
- [ ] Implement Redis caching for frequent queries
- [ ] Use asyncpg driver

### Database (Supabase)
- [ ] Enable connection pooling (Transaction mode)
- [ ] Set pool_size to 40% of max_connections
- [ ] Verify pg_bouncer settings in dashboard
- [ ] Index frequently queried columns

### Monitoring
- [ ] Enable Vercel Speed Insights
- [ ] Set up Railway metrics dashboard
- [ ] Monitor Supabase connection pool usage

---

## 7. Expected Performance Gains

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| FCP (First Contentful Paint) | 2.5s | <1.5s | 40% |
| Bundle size | 800KB | <500KB | 37% |
| API latency (Asia) | 300ms | <200ms | 33% |
| DB connections | Direct (slow) | Pooled | 50% |

---

## Unresolved Questions

1. **Railway region:** Is Singapore the closest to Vietnam users, or would another region be better?
2. **Vercel bandwidth:** Will 100GB/month suffice for expected traffic?
3. **Supabase limits:** When to upgrade from free tier (500MB DB limit)?
4. **WebSocket latency:** Does chat feature need dedicated optimization?
5. **Image hosting:** Should images be on Supabase storage or external CDN?
