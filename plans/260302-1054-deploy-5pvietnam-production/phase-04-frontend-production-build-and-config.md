# Phase 4: Frontend Production Build & Config

## Context Links
- [Frontend vite.config.js](../../frontend/vite.config.js)
- [Frontend vercel.json](../../frontend/vercel.json)
- [Frontend package.json](../../frontend/package.json)

## Overview
- **Priority**: P1
- **Status**: pending
- **Effort**: 30 min
- **Description**: Configure frontend for production: set API URL, verify build, test API connectivity, ensure SPA routing works

## Key Insights
- 8 files reference `VITE_API_URL` with fallback to `http://localhost:8000`
- `vercel.json` already has SPA rewrite rules
- Vite build output is `dist/` by default
- React 19.2.0 + Vite 7.2.4 (modern stack, no special config needed)
- API URL is baked into the build at compile time (Vite env vars)

## Requirements

### Functional
- `VITE_API_URL` set to `https://api.5pvietnam.com` in Vercel env vars
- `npm run build` succeeds without errors
- All API calls from frontend reach backend correctly
- SPA routing works (direct URL access to any route returns index.html)

### Non-Functional
- Build size reasonable (< 2MB gzipped)
- First Contentful Paint < 3s on 3G connection

## Architecture

```
Vercel CDN (global edge)
  └── dist/
      ├── index.html (SPA entry)
      ├── assets/
      │   ├── index-xxx.js  (React bundle)
      │   └── index-xxx.css (styles)
      └── [other static assets]

API calls: fetch("https://api.5pvietnam.com/api/...")
```

## Related Code Files

### Files Using VITE_API_URL (no modifications needed)
- `frontend/src/App.jsx` (line 9)
- `frontend/src/hooks/useChatSession.js` (line 4)
- `frontend/src/contexts/AuthContext.jsx` (line 10)
- `frontend/src/components/SearchBox.jsx` (line 10)
- `frontend/src/components/admin/AdminPanel.jsx` (line 15)
- `frontend/src/components/admin/RateUploadModal.jsx` (line 9)
- `frontend/src/components/admin/RateFormModal.jsx` (line 9)
- `frontend/src/components/chat/SearchDropdown.jsx` (line 5)

### Files to Review (no changes expected)
- `frontend/vite.config.js` - Minimal config (React plugin only); sufficient
- `frontend/vercel.json` - SPA rewrite; already correct

## Implementation Steps

### 1. Set Vercel Environment Variable
In Vercel Dashboard > Project > Settings > Environment Variables:
```
VITE_API_URL = https://api.5pvietnam.com
```
Set for **Production** environment. Optionally set `http://localhost:8000` for **Development** environment.

### 2. Verify Local Build
```bash
cd frontend
VITE_API_URL=https://api.5pvietnam.com npm run build
```
- Check no build errors
- Check `dist/` directory is generated
- Check bundle size: `du -sh dist/`

### 3. Test SPA Routing
After Vercel deploy:
- Navigate to `https://5pvietnam.com/` (root)
- Navigate to `https://5pvietnam.com/admin` (deep link)
- Navigate to `https://5pvietnam.com/some-nonexistent-path` (should show app, not 404)
- All should serve `index.html` and React router handles routing

### 4. Test API Connectivity
After DNS is configured (Phase 2) and backend is deployed (Phase 1):
1. Open browser DevTools > Network tab
2. Load `https://5pvietnam.com`
3. Verify API calls go to `https://api.5pvietnam.com/api/...`
4. Verify no CORS errors in console
5. Test login flow (auth endpoint)
6. Test chat functionality (chat endpoint)
7. Test job listing (jobs endpoint)

### 5. Performance Check
```bash
# Lighthouse audit (optional)
npx lighthouse https://5pvietnam.com --output=json --only-categories=performance
```

## Todo List
- [ ] Set `VITE_API_URL` env var in Vercel (Production)
- [ ] Verify `npm run build` succeeds locally with production API URL
- [ ] Deploy to Vercel (auto or manual trigger)
- [ ] Test SPA routing on all routes
- [ ] Test API connectivity (no CORS errors)
- [ ] Test auth flow end-to-end
- [ ] Test chat functionality end-to-end
- [ ] Check bundle size is reasonable

## Success Criteria
- `https://5pvietnam.com` loads the React app
- All API calls resolve to `api.5pvietnam.com` (check Network tab)
- No CORS errors in browser console
- SPA deep links work (e.g., `/admin`, `/jobs`)
- Login + Chat + Job CRUD all functional

## Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| VITE_API_URL not baked into build | Low | High | Verify in Vercel build logs; env var must start with `VITE_` |
| Mixed content (HTTP/HTTPS) | Low | Medium | Backend enforces HTTPS; all URLs use `https://` |
| Bundle too large | Low | Low | Vite tree-shaking handles this; React 19 is lean |

## Security Considerations
- No secrets in frontend code (only `VITE_API_URL` which is public)
- All auth tokens stored in memory/localStorage by AuthContext
- API calls use `credentials: true` for cookie/JWT auth
- No source maps in production (Vite default)

## Next Steps
- After frontend works end-to-end: proceed to Phase 5 (CI/CD & Monitoring)
- Consider adding error boundary component for production error handling
- Consider adding a loading/maintenance page for deploy windows
