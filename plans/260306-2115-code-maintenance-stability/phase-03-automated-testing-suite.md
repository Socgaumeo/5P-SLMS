# Phase 3: Automated Testing Suite

## Context Links
- Parent: [plan.md](plan.md)
- Depends on: [Phase 2](phase-02-cicd-quality-gate.md)
- Research: [Code Maintenance Report](../reports/researcher-260306-2109-code-maintenance-stability.md)

## Overview
- **Date**: 2026-03-06
- **Priority**: HIGH
- **Status**: pending
- **Description**: Write pytest test suite covering critical API routes (auth, jobs, chat, quotations). Target 70%+ coverage on critical paths. Use httpx async client for FastAPI testing.

## Key Insights
- No automated tests currently — all testing is manual
- Focus on critical paths first: auth (login), jobs (CRUD), chat (AI), quotations
- Use `httpx.AsyncClient` with `app` for in-process testing (fast, no network)
- Mock Supabase calls for unit tests, real calls for integration tests
- AI chat tests should mock LLM responses to avoid API costs
- **CRITICAL**: Python test files MUST use `test_*.py` naming (snake_case). Pytest does NOT discover `test-*.py` (kebab-case). Using wrong names means CI passes with 0 tests collected — silently broken.
- **CRITICAL**: Verify `app` is exported at module level in `main.py` before writing conftest.py fixture. Run: `python -c "from main import app; print(type(app))"`
- **Test isolation**: Use mock Supabase (Pattern 3) or separate test Supabase project to avoid polluting production DB
<!-- Updated: Improvement Merge - #1 snake_case test file names, app import verification, test isolation -->

## Requirements

### Functional
- F1: Test suite for auth endpoints (login, token refresh, protected routes)
- F2: Test suite for job endpoints (create, list, update status)
- F3: Test suite for chat endpoints (send message, create booking via chat)
- F4: Test suite for quotation endpoints (CRUD)
- F5: Shared fixtures for auth tokens, mock data

### Non-Functional
- NF1: 70%+ coverage on critical API routes
- NF2: All tests run in <60 seconds
- NF3: No external API calls in unit tests (mock LLM, mock Supabase)
- NF4: Tests are deterministic (no flaky tests)

## Related Code Files

### Files to Create
- `backend/tests/conftest.py` - Shared fixtures (auth, client, mock data)
- `backend/tests/test_auth.py` - Auth endpoint tests (MUST use snake_case, NOT kebab-case)
- `backend/tests/test_jobs.py` - Job CRUD tests
- `backend/tests/test_chat.py` - Chat + AI tests
- `backend/tests/test_quotations.py` - Quotation CRUD tests
<!-- Updated: Improvement Merge - #1 Renamed test files from kebab-case to snake_case for pytest discovery -->

### Files to Read (Reference)
- `backend/main.py` - App instance + route registration
- `backend/app/api/auth.py` - Auth endpoints
- `backend/app/api/jobs.py` - Job endpoints
- `backend/app/api/chat.py` - Chat endpoints
- `backend/app/api/quotations.py` - Quotation endpoints

## Implementation Steps

1. **Pre-check: Verify app export** (run before writing tests)
   ```bash
   cd backend && python -c "from main import app; print(type(app))"
   # Expected: <class 'fastapi.applications.FastAPI'>
   ```
   - If factory pattern: adjust conftest to call `create_app()`
   - If conditional init: refactor so `app` is available at module level

2. **Add pytest config** to `backend/pyproject.toml`
   ```toml
   [tool.pytest.ini_options]
   testpaths = ["tests"]
   python_files = ["test_*.py"]      # Only test_*.py pattern (NOT test-*.py)
   python_classes = ["Test*"]
   python_functions = ["test_*"]
   asyncio_mode = "auto"             # For FastAPI async tests
   ```
<!-- Updated: Improvement Merge - #1 pytest discovery config -->

3. **Create shared test fixtures** (`backend/tests/conftest.py`)
   - `client` fixture: `httpx.AsyncClient(app=app)`
   - `auth_token` fixture: login with test user, return JWT
   - `auth_headers` fixture: `{"Authorization": f"Bearer {token}"}`
   - `mock_supabase` fixture: patch Supabase client for isolated tests (prevent production DB pollution)
   ```python
   # Pattern: Mock Supabase completely (safest, no production DB risk)
   from unittest.mock import AsyncMock, patch

   @pytest.fixture
   def mock_supabase():
       with patch('app.db.supabase_client.supabase') as mock:
           mock.table.return_value.select.return_value.execute.return_value.data = []
           yield mock
   ```
   - `sample_job` fixture: valid job creation payload
   - `sample_quotation` fixture: valid quotation payload
<!-- Updated: Improvement Merge - Added mock Supabase fixture for test isolation -->

4. **Auth tests** (`backend/tests/test_auth.py`)
   - Test login with valid credentials → 200 + JWT token
   - Test login with wrong password → 401
   - Test login with nonexistent email → 401
   - Test protected route without token → 401
   - Test protected route with expired token → 401
   - Test protected route with valid token → 200

3. **Job tests** (`backend/tests/test_jobs.py`)
   - Test list jobs (authenticated) → 200 + array
   - Test create job with valid data → 201
   - Test create job with missing fields → 422
   - Test update job status → 200
   - Test get job by ID → 200
   - Test search/filter jobs → 200

4. **Chat tests** (`backend/tests/test_chat.py`)
   - Test send message (authenticated) → 200 + AI response
   - Mock LLM client to return predictable response
   - Test conversation history maintained
   - Test booking creation via chat entities
   - Test error handling when LLM fails → 500 with message

5. **Quotation tests** (`backend/tests/test_quotations.py`)
   - Test CRUD operations for quotations
   - Test search with filters
   - Test rate calculations

## Todo List
- [ ] Create `backend/tests/conftest.py` with shared fixtures
- [ ] Write auth endpoint tests (6 test cases)
- [ ] Write job endpoint tests (6 test cases)
- [ ] Write chat endpoint tests (5 test cases)
- [ ] Write quotation endpoint tests (5 test cases)
- [ ] Run full suite, verify all pass
- [ ] Check coverage report: `pytest --cov=app --cov-report=html`
- [ ] Fix any failures or flaky tests

## Success Criteria
- 22+ test cases across 4 test files
- All tests pass deterministically
- 70%+ coverage on critical API routes
- Tests complete in <60 seconds
- No external API calls during test run

## Risk Assessment
- **Risk**: Mocking Supabase is complex → **Mitigation**: Start with integration tests against real Supabase, add mocks incrementally
- **Risk**: AI chat tests are unpredictable → **Mitigation**: Mock LLM responses with fixed JSON
- **Risk**: Test data pollutes production DB → **Mitigation**: Use separate test schema or cleanup after each test

## Security Considerations
- Test credentials stored in environment, not hardcoded
- Test data cleaned up after test run
- No real user data used in tests

## Next Steps
- Phase 4: Pre-commit hooks and code quality automation
