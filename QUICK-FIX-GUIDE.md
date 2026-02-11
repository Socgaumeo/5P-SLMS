# Quick Fix Guide - 5P-SLMS Issues

**Date**: 2026-02-05
**Issues**: Duplicate logo, Hamburger menu, Search not working

---

## 🔴 CRITICAL: Search Not Working (Job #0008, Customer "sevt")

**Root Cause**: Supabase database is unreachable (DNS resolution failure)

### Test the Issue
```bash
cd backend
python3 test-database-connection.py
```

### Fix Options

#### Option A: Check Supabase Dashboard (RECOMMENDED)
1. Go to https://supabase.com/dashboard
2. Find project with ID: `vpmsytbbsxmtdicnkytv`
3. Check if project is:
   - ❌ Paused → Click "Resume project"
   - ❌ Deleted → Restore from backup or create new
   - ❌ Moved → Get new DATABASE_URL from settings
4. Get correct DATABASE_URL from: Project Settings → Database → Connection String
5. Update the URL (see Option B)

#### Option B: Update Database Connection String
```bash
# Create .env file in project root
cd /Users/bear1108/Documents/GitHub/5P-SLMS
cat > .env << 'EOF'
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@YOUR_NEW_HOST:5432/postgres
EOF
```

Or directly edit `backend/app/core/config.py` line 14:
```python
DATABASE_URL: str = "postgresql://postgres:PASSWORD@NEW_HOST:5432/postgres"
```

#### Option C: Use Local PostgreSQL (Development)
```bash
# Install PostgreSQL
brew install postgresql@14
brew services start postgresql@14

# Create database
createdb slms_dev

# Update .env
echo 'DATABASE_URL=postgresql://localhost:5432/slms_dev' > .env

# You'll need to restore schema and data
```

### After Fixing Database Connection

1. **Restart Backend**:
   ```bash
   # Find and kill existing process
   ps aux | grep uvicorn
   kill <PID>

   # Start fresh
   cd backend
   python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Test Again**:
   ```bash
   python3 test-database-connection.py
   curl "http://localhost:8000/api/search/jobs?q=0008"
   ```

3. **Test in Browser**:
   - Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows/Linux)
   - Search for "0008" or "sevt"
   - Should show dropdown with results

---

## 🟡 Hamburger Menu Not Working

**Status**: Code looks correct - likely browser cache issue

### Quick Fix
1. **Hard refresh browser**: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows/Linux)
2. **Test in incognito mode**: See if it works there
3. **Check browser console**:
   - Open DevTools: `F12` or `Cmd+Option+I`
   - Click hamburger menu (☰)
   - Look for JavaScript errors in Console tab

### If Still Not Working
Add debug logging to check state changes:

```bash
cd /Users/bear1108/Documents/GitHub/5P-SLMS/frontend/src
```

Edit `App.jsx` around line 1934, change:
```jsx
<button className="menu-toggle" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button>
```

To:
```jsx
<button
  className="menu-toggle"
  onClick={() => {
    console.log('🍔 Menu clicked! Current state:', sidebarOpen);
    setSidebarOpen(!sidebarOpen);
  }}
>
  ☰
</button>
```

Then check browser console when clicking the menu.

---

## 🟢 Duplicate Logo Issue

**Status**: NOT FOUND in code - no duplicate exists

### Investigation Result
- Code review shows **only ONE logo** in sidebar
- Header contains: hamburger menu, search box, user menu (no logo)
- Files checked: `frontend/src/App.jsx` lines 1884-1892, 1932-1947

### If You Still See Two Logos
1. **Hard refresh**: `Cmd+Shift+R` - might be cached old version
2. **Take screenshot**: Show where both logos appear
3. **Check browser DevTools**:
   - Right-click on each logo → "Inspect"
   - See if they have same CSS class or are different elements

**Possible causes if issue persists**:
- Browser caching old version
- CSS rendering duplicate
- Different component loaded in production vs development

---

## Quick Test Checklist

After applying fixes, test:

- [ ] Database connection: `python3 backend/test-database-connection.py` → Should pass all tests
- [ ] Search API: `curl "http://localhost:8000/api/search/jobs?q=0008"` → Should return JSON
- [ ] Frontend search: Type "0008" in search box → Should show dropdown results
- [ ] Hamburger menu: Click ☰ button → Sidebar should collapse/expand
- [ ] Logo count: Check header and sidebar → Should only see ONE logo

---

## Need More Help?

**For Database Issues**:
- Check Supabase dashboard status
- Verify DATABASE_URL is correct
- Check network/firewall settings
- Consider local PostgreSQL for development

**For UI Issues**:
- Clear all browser cache
- Test in incognito/private mode
- Check browser console for errors
- Use React DevTools to inspect component state

**Debug Reports**:
- Full analysis: `plans/reports/debugger-260205-0833-ui-and-search-issues.md`
- Database test: `backend/test-database-connection.py`

---

## Summary

| Issue | Severity | Status | Action |
|-------|----------|--------|--------|
| Search not working | 🔴 CRITICAL | Database unreachable | Fix Supabase connection |
| Hamburger menu | 🟡 MEDIUM | Code correct | Clear browser cache |
| Duplicate logo | 🟢 LOW | Not found in code | Hard refresh or provide screenshot |

**Priority**: Fix database connection first → everything else is minor.
