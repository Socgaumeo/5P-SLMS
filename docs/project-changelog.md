# Project Changelog

## [2026-03-02] - Security, Speed, and Parser Improvements

### Security
- **JWT Authentication**: Added `Depends(verify_jwt)` to 13 endpoints in `main.py` (quotations, jobs, admin, files)
- **Router-Level Auth**: Implemented `require_manager_or_admin` middleware in `admin.py` for protected routes
- **Security Headers Middleware**: Added `SecurityHeadersMiddleware` (HSTS, X-Frame-Options, X-Content-Type-Options, CSP)
- **Rate Limiting**: Configured slowapi with 100 requests/min default and 5 requests/min for login endpoint
- **Input Sanitization**: Added sanitization on search endpoints to prevent injection attacks
- **Password Policy**: Enforced minimum 8-character password requirement (previously 6)

### Speed Optimization
- **Vercel Speed Insights**: Integrated frontend performance monitoring via Vercel SDK
- **Bundle Splitting**: Configured Vite manual chunks with separate vendor-react bundle
- **Compression**: Added `GZipMiddleware` to backend for API response compression

### Parser Enhancements
- **Confidence-Based AI Fallback**: Triggers AI-powered parser when extraction confidence < 60%
- **Surcharge Extraction**: Extended parser to extract surcharge data from rate sheets
- **Data Model Update**: Added `is_surcharge` field to `RateRow` model
- **Prompt Enhancement**: Updated AI parser prompt to include surcharge and notes extraction

### Related Files
- `backend/main.py` — Auth endpoints, middleware setup
- `backend/app/api/admin.py` — Router-level auth
- `backend/app/ai/unified_logistics_prompt.py` — Enhanced parser prompt
- `backend/app/models.py` — `RateRow.is_surcharge` field
- `frontend/vite.config.ts` — Bundle splitting config

### Impact
- **Security**: All API endpoints now authenticated; request rate-limited; headers hardened
- **Performance**: Frontend bundle optimized; API responses compressed
- **Parser Accuracy**: AI fallback improves extraction reliability for complex rate sheets
