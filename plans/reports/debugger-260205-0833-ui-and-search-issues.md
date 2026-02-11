# Debug Report: UI and Search Issues in 5P-SLMS

**Date**: 2026-02-05
**Reporter**: Debugger Agent
**Environment**: macOS (Darwin 25.2.0)
**Work Context**: /Users/bear1108/Documents/GitHub/5P-SLMS

---

## Executive Summary

Investigated 3 reported issues in 5P-SLMS application:
1. **Duplicate logo** - NOT CONFIRMED (no duplicate found in code)
2. **Hamburger menu not working** - Code appears correct, likely browser cache issue
3. **Search not working** - ROOT CAUSE IDENTIFIED: Database connection failure

**Critical Finding**: Supabase database is unreachable due to DNS resolution failure. This is blocking ALL search functionality.

---

## Issue Analysis

### Issue 1: Duplicate Logo in Header/Sidebar

**Status**: NOT REPRODUCED IN CODE

**Investigation**:
- Examined `frontend/src/App.jsx` lines 1880-1947
- Logo only appears in sidebar (`.sidebar-logo` div, lines 1884-1892)
- Header contains: hamburger menu, page title, search box, user menu
- NO logo element found in header section

**Files Examined**:
- `/Users/bear1108/Documents/GitHub/5P-SLMS/frontend/src/App.jsx`
- `/Users/bear1108/Documents/GitHub/5P-SLMS/frontend/src/App.css`

**Finding**: Code shows single logo in sidebar only. If user sees duplicate, possible causes:
- Browser caching old version
- CSS rendering issue
- Screenshot/description mismatch

**Recommendation**:
- User should hard refresh browser (Cmd+Shift+R on Mac)
- Verify with latest code deployment
- Request screenshot if issue persists

---

### Issue 2: Hamburger Menu Toggle Not Working

**Status**: CODE APPEARS CORRECT

**Investigation**:
- Hamburger button located at `App.jsx` line 1934
- Click handler: `onClick={() => setSidebarOpen(!sidebarOpen)}`
- State management: `const [sidebarOpen, setSidebarOpen] = useState(true)` (line 1713)
- CSS transitions defined in `App.css`:
  - `.sidebar` has `transition: width 0.3s ease`
  - `.sidebar.collapsed` sets width to `var(--sidebar-collapsed)`
  - `.main-content` has `transition: margin-left 0.3s ease`

**Code Structure**:
```jsx
// State
const [sidebarOpen, setSidebarOpen] = useState(true)

// Sidebar
<aside className={`sidebar ${sidebarOpen ? 'open' : 'collapsed'}`}>

// Main content
<main className={`main-content ${sidebarOpen ? '' : 'expanded'}`}>

// Toggle button
<button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button>
```

**Finding**: Implementation is correct. Toggle should work.

**Possible Causes**:
1. React state not updating (requires browser console inspection)
2. CSS not loaded properly
3. JavaScript error preventing state update
4. Browser cache issue

**Recommendation**:
- Check browser console for JavaScript errors
- Hard refresh browser
- Test in incognito mode
- Verify React DevTools shows state changing on click

---

### Issue 3: Search Not Working (Job #0008, Customer "sevt")

**Status**: ROOT CAUSE IDENTIFIED - DATABASE CONNECTION FAILURE

**Investigation Steps**:

1. **Frontend Code Review** (`frontend/src/components/SearchBox.jsx`):
   - Search triggers on 2+ characters
   - Makes API call: `${API_URL}/api/search/jobs?q=${encodeURIComponent(searchQuery)}&limit=10`
   - Default API_URL: `http://localhost:8000`
   - Frontend code is correct

2. **Backend API Review** (`backend/app/api/search.py`):
   - Endpoint: `/api/search/jobs`
   - SQL query uses ILIKE with `%{q}%` pattern matching
   - Searches: job_no, customer_code, customer short_name, company_name
   - Query structure is correct

3. **API Testing**:
   ```bash
   curl "http://localhost:8000/api/search/jobs?q=0008&limit=10"
   # Result: HTTP/1.1 500 Internal Server Error
   ```

4. **Database Connection Test**:
   ```python
   # Test direct database connection
   from app.db.session import get_connection
   conn = get_connection()

   # Result:
   # psycopg2.OperationalError: could not translate host name
   # "db.vpmsytbbsxmtdicnkytv.supabase.co" to address:
   # nodename nor servname provided, or not known
   ```

5. **DNS Resolution Test**:
   ```bash
   ping db.vpmsytbbsxmtdicnkytv.supabase.co
   # Result: ping: cannot resolve ... Unknown host

   nslookup db.vpmsytbbsxmtdicnkytv.supabase.co
   # Result: Can't find ... No answer

   ping supabase.co
   # Result: SUCCESS (76.76.21.21)
   ```

**ROOT CAUSE**: Supabase database host `db.vpmsytbbsxmtdicnkytv.supabase.co` cannot be resolved via DNS.

**Evidence**:
- Backend running: ✅ (PID 91530, uvicorn on port 8000)
- Internet connectivity: ✅ (supabase.co resolves)
- Supabase subdomain: ❌ (DNS returns "No answer")
- Database connection: ❌ (psycopg2.OperationalError)

**Technical Details**:
- Database URL (from `backend/app/core/config.py` line 14):
  ```
  postgresql://postgres:[REDACTED]@db.vpmsytbbsxmtdicnkytv.supabase.co:5432/postgres
  ```
- Connection failure propagates as 500 Internal Server Error
- Frontend shows "Không tìm thấy kết quả" (no results) message

---

## Impact Assessment

| Issue | Severity | Impact | Users Affected |
|-------|----------|--------|----------------|
| Duplicate Logo | Low | UI aesthetics | All (if real) |
| Hamburger Menu | Medium | Navigation UX | All |
| Search Function | **CRITICAL** | Core functionality blocked | **ALL USERS** |

**Business Impact**:
- Search is completely non-functional
- Users cannot find jobs by job number or customer code
- Manual navigation required for all job access
- Severely impacts operational efficiency

---

## Recommended Solutions

### Issue 1: Duplicate Logo
**Action**: None required (not found in code)
**If persists**: Request screenshot for further investigation

### Issue 2: Hamburger Menu
**Immediate Actions**:
1. Clear browser cache and hard refresh
2. Check browser console for JS errors
3. Test in incognito mode

**If Still Broken**:
```jsx
// Add debugging to App.jsx
<button
  className="menu-toggle"
  onClick={() => {
    console.log('Toggle clicked, current state:', sidebarOpen);
    setSidebarOpen(!sidebarOpen);
  }}
>
  ☰
</button>
```

### Issue 3: Search Function (CRITICAL)

**Root Cause**: Supabase database DNS resolution failure

**Possible Reasons**:
1. Supabase project paused/deleted
2. Database URL typo in config
3. Supabase regional DNS issue
4. Project migrated to different URL

**Immediate Actions**:

**Option A: Verify Supabase Project Status**
1. Log into Supabase dashboard at https://supabase.com
2. Check if project `vpmsytbbsxmtdicnkytv` exists and is active
3. Verify database connection string in project settings
4. If project paused, unpause it
5. If project deleted, restore from backup or create new

**Option B: Update Database Connection String**
1. Get correct database URL from Supabase dashboard
2. Update `backend/app/core/config.py` or create `.env` file:
   ```bash
   # In project root: /Users/bear1108/Documents/GitHub/5P-SLMS/.env
   DATABASE_URL=postgresql://postgres:PASSWORD@NEW-HOST:5432/postgres
   ```
3. Restart backend server

**Option C: Test Connection Manually**
```bash
cd /Users/bear1108/Documents/GitHub/5P-SLMS/backend
python3 -c "
from app.db.session import get_connection
conn = get_connection()
print('Connection successful!')
conn.close()
"
```

**Option D: Use Local Database (Development)**
If Supabase unavailable, set up local PostgreSQL:
```bash
# Install PostgreSQL
brew install postgresql@14

# Start service
brew services start postgresql@14

# Create database
createdb slms_dev

# Update .env
DATABASE_URL=postgresql://localhost:5432/slms_dev

# Run migrations to restore schema
```

---

## Testing Verification

After implementing fixes, verify with:

**Test 1: Database Connection**
```bash
cd backend
python3 -c "from app.db.session import get_connection; conn = get_connection(); print('OK')"
```

**Test 2: Search API**
```bash
curl "http://localhost:8000/api/search/jobs?q=0008&limit=10"
# Should return JSON with results array
```

**Test 3: Frontend Search**
1. Open browser to `http://localhost:5173` (or frontend URL)
2. Click search box in header
3. Type "0008" or "sevt"
4. Verify dropdown shows results

**Test 4: Hamburger Menu**
1. Click hamburger menu (☰) button
2. Verify sidebar collapses/expands smoothly
3. Check main content area adjusts width

---

## Files Referenced

**Frontend**:
- `/Users/bear1108/Documents/GitHub/5P-SLMS/frontend/src/App.jsx` (lines 1713-1947)
- `/Users/bear1108/Documents/GitHub/5P-SLMS/frontend/src/App.css` (lines 63-223)
- `/Users/bear1108/Documents/GitHub/5P-SLMS/frontend/src/components/SearchBox.jsx` (all)

**Backend**:
- `/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/api/search.py` (lines 139-180)
- `/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/db/session.py` (lines 43-48)
- `/Users/bear1108/Documents/GitHub/5P-SLMS/backend/app/core/config.py` (line 14)

---

## Unresolved Questions

1. **Duplicate Logo**: Is this visible in production or specific browser? (Need screenshot)
2. **Hamburger Menu**: Are there JS errors in browser console when clicking?
3. **Supabase**: Was project intentionally paused or URL changed?
4. **Database**: Do we have backup of database schema/data if project was deleted?
5. **Environment**: Should we use local database for development vs Supabase for production?

---

## Next Steps

**Priority 1 (CRITICAL)**: Resolve database connectivity
- Contact Supabase admin or check dashboard
- Update DATABASE_URL if needed
- Consider local PostgreSQL setup for dev environment

**Priority 2 (HIGH)**: Verify hamburger menu with user
- Request console logs
- Test after cache clear

**Priority 3 (LOW)**: Clarify duplicate logo issue
- Request screenshot or video
- Verify deployment matches current code

---

## Summary

**Working**: Backend server, frontend app, code structure
**Broken**: Database connectivity → search completely non-functional
**Unclear**: Duplicate logo (not in code), hamburger menu (code correct)

**Critical Path**: Fix Supabase connection to restore search functionality. UI issues appear to be client-side caching or environment-specific.
