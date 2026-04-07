# System Architecture

## Overview
5P SLMS is a logistics management platform with AI-powered rate sheet parsing, quotation management, and administrative controls. The system emphasizes security, performance, and intelligent data extraction.

## Backend Architecture

### Authentication & Authorization Layer
- **JWT Verification**: All API endpoints require JWT tokens via `verify_jwt` dependency
- **Role-Based Access Control**: Admin and manager roles enforce endpoint-level authorization
- **Protected Routes**: Admin router requires `require_manager_or_admin` middleware
- **Password Policy**: Minimum 8 characters enforced at user creation/update

### Security Middleware Stack
```
Request → SecurityHeadersMiddleware → Auth Check → GZipMiddleware → Handler
```

**SecurityHeadersMiddleware** sets:
- `Strict-Transport-Security` (HSTS) — Forces HTTPS
- `X-Frame-Options: DENY` — Prevents clickjacking
- `X-Content-Type-Options: nosniff` — Prevents MIME-sniffing
- `Content-Security-Policy` — Controls resource loading

### Rate Limiting
- **Default**: 100 requests/minute per IP
- **Login**: 5 requests/minute (stricter for auth attempts)
- Implemented via slowapi

### Input Handling
- Search endpoints sanitize user input to prevent injection
- File uploads validated at upload handler level

## API Endpoints

### Quotation Endpoints (all require JWT)
- `GET /api/quotations` — List quotations
- `POST /api/quotations` — Create quotation
- `GET /api/quotations/{id}` — Get quotation detail
- `PUT /api/quotations/{id}` — Update quotation
- `DELETE /api/quotations/{id}` — Delete quotation

### Job Management (all require JWT)
- `GET /api/jobs` — List jobs
- `POST /api/jobs` — Create job
- `GET /api/jobs/{id}` — Get job detail
- `PATCH /api/jobs/{id}` — Update job status

### Admin Routes (require manager/admin role)
- `GET /api/admin/users` — List users
- `POST /api/admin/users` — Create user
- `PUT /api/admin/users/{id}` — Update user
- `DELETE /api/admin/users/{id}` — Delete user

### File Management (require JWT)
- `POST /api/files/upload` — Upload rate sheet
- `GET /api/files/{id}` — Download file

## Rate Sheet Parser

### Two-Stage Parsing Strategy
1. **Standard Parser** (Python-based regex/table extraction)
   - Fast, reliable for standard rate sheet formats
   - Returns confidence score (0-100)

2. **AI Fallback Parser** (Claude API)
   - Triggered when confidence < 60%
   - Handles complex, unstructured rate sheets
   - Extracts: routes, rates, surcharges, notes

### Data Model
**RateRow** contains:
- `origin`, `destination`, `service_type_code`
- `base_rate`, `surcharge` (new)
- `is_surcharge` (boolean flag, new)
- `confidence_score`, `source` (standard vs. AI)

### Parser Prompt Enhancement
AI parser includes instructions for:
- Surcharge identification and extraction
- Notes/remarks extraction
- Ambiguity handling and confidence reporting

## Frontend Architecture

### Performance Optimization
- **Vite Manual Chunks**: Separate vendor-react bundle reduces initial load
- **Compression**: Backend GZipMiddleware compresses API responses
- **Speed Monitoring**: Vercel Speed Insights integrated for performance tracking

### Bundle Structure
```
main.js        — App code, routes, utilities
vendor-react.js — React, ReactDOM, dependencies
```

## Data Flow

### Rate Sheet Upload & Processing
```
User Upload → File Validator → Standard Parser → Confidence Check
                                                      ↓
                                            Confidence >= 60%? → Store Results
                                                      ↓ No
                                            AI Parser → Store Results
```

### Authentication Flow
```
User Login → Password Verify → JWT Generated → Include in Headers → API Access
                                                   ↓ Invalid
                                              Rate Limited (5/min)
```

## Deployment Considerations
- HTTPS enforced via HSTS headers
- Rate limiting protects against brute force
- GZip compression reduces bandwidth
- JWT tokens expire (check config for TTL)

## Security Posture
- All endpoints authenticated
- CORS headers applied
- Input sanitized on search
- Rate limited on sensitive endpoints
- Security headers hardened
- Passwords meet 8-char minimum
