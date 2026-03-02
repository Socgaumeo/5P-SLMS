# Phase 1: Bảo mật Backend

## Context Links
- [Plan tổng](plan.md)
- [Báo cáo security review](../reports/security-review-260302-1112-full-project.md)
- [dependencies.py](../../backend/app/api/dependencies.py) — Đã có `get_current_user`, `require_admin`, `require_manager_or_admin`

## Tổng quan
- **Ngày**: 2026-03-02
- **Ưu tiên**: P0 - CRITICAL
- **Trạng thái**: completed
- **Mô tả**: Thêm authentication/authorization cho tất cả endpoints đang mở, thêm rate limiting, sanitize input

## Phát hiện quan trọng

1. `dependencies.py` ĐÃ CÓ các dependency sẵn: `get_current_user`, `require_admin`, `require_manager_or_admin`
2. Frontend `AuthContext.jsx` ĐÃ gửi `Authorization: Bearer <token>` header
3. Chỉ cần thêm `Depends()` vào các endpoint — KHÔNG cần viết logic auth mới
4. `main.py` có ~15 endpoints KHÔNG có auth (assign, status, cancel, delete service, notes, search, list)

## Yêu cầu

### Chức năng
- Tất cả endpoints thay đổi dữ liệu phải yêu cầu đăng nhập
- Admin endpoints (CRUD rates/vendors/customers) phải yêu cầu role ADMIN hoặc MANAGER
- Search/list endpoints cho phép đọc nếu đã đăng nhập (bất kỳ role)
- Login endpoint không cần auth (tất nhiên)

### Phi chức năng
- Rate limiting: 100 req/phút cho API chung, 5 req/phút cho login
- Sanitize input trong search filters
- Security headers (HSTS, X-Frame-Options, X-Content-Type-Options)

## File liên quan

| File | Hành động | Mô tả |
|------|-----------|-------|
| `backend/app/api/dependencies.py` | Giữ nguyên | Đã có auth dependencies |
| `backend/main.py` | **SỬA** | Thêm Depends() cho 15 endpoints, thêm security headers middleware |
| `backend/app/api/admin.py` | **SỬA** | Thêm Depends(require_admin) cho tất cả CRUD endpoints |
| `backend/app/api/rate_file_upload.py` | **SỬA** | Thêm Depends(require_manager_or_admin) cho upload/import |
| `backend/app/api/auth.py` | **SỬA** | Tăng password policy từ 6 → 8 ký tự |
| `backend/requirements.txt` | **SỬA** | Thêm `slowapi` cho rate limiting |
| `backend/app/middleware/security-headers.py` | **TẠO MỚI** | Middleware thêm security headers |
| `backend/app/middleware/rate-limiter.py` | **TẠO MỚI** | Rate limiting với slowapi |

## Các bước thực hiện

### Bước 1: Thêm security headers middleware
Tạo `backend/app/middleware/security-headers.py`:
```python
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response
```

### Bước 2: Thêm rate limiting
Tạo `backend/app/middleware/rate-limiter.py`:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
# Dùng: @limiter.limit("100/minute") trên endpoint
```

Thêm `slowapi` vào `requirements.txt`

### Bước 3: Bảo vệ endpoints trong main.py
Thêm `Depends(get_current_user)` cho TẤT CẢ endpoints thay đổi dữ liệu:
```python
from app.api.dependencies import get_current_user, require_admin

@app.put("/api/services/{svc_id}/assign")
async def assign_service(svc_id: int, request: AssignServiceRequest,
                         current_user: dict = Depends(get_current_user)):
```

Endpoints cần bảo vệ trong `main.py`:
- `PUT /api/services/{svc_id}/assign` → `get_current_user`
- `PUT /api/services/{svc_id}/status` → `get_current_user`
- `DELETE /api/services/{svc_id}` → `require_manager_or_admin`
- `PUT /api/services/{svc_id}/notes` → `get_current_user`
- `PUT /api/jobs/{job_id}/status` → `get_current_user`
- `DELETE /api/jobs/{job_id}/cancel` → `require_manager_or_admin`
- `GET /api/customers` → `get_current_user` (đọc cũng cần đăng nhập)
- `GET /api/vendors` → `get_current_user`
- `GET /api/employees` → `get_current_user`
- `GET /api/search/customers` → `get_current_user`
- `GET /api/search/vendors` → `get_current_user`
- `GET /api/dashboard/stats` → `get_current_user`

### Bước 4: Bảo vệ admin.py
Thêm `dependencies=[Depends(require_admin)]` vào router level hoặc từng endpoint:
```python
router = APIRouter(prefix="/api/admin", tags=["Admin"],
                   dependencies=[Depends(require_manager_or_admin)])
```

### Bước 5: Sanitize search input
Trong `main.py` search endpoints, sanitize query parameter:
```python
import re
q_safe = re.sub(r'[,.()*;\'"]', '', q).strip()[:100]
```

### Bước 6: Tăng password policy
Trong `auth.py` line 211, đổi `6` → `8` và thêm kiểm tra complexity:
```python
if len(new_password) < 8:
    raise HTTPException(400, "Mật khẩu mới phải có ít nhất 8 ký tự")
```

### Bước 7: Đăng ký middleware trong main.py
```python
from app.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)
```

## Checklist
- [x] Tạo security headers middleware
- [x] Tạo rate limiter middleware
- [x] Thêm auth cho 12 endpoints trong main.py
- [x] Thêm auth cho admin.py router
- [x] Thêm auth cho rate_file_upload.py
- [x] Sanitize search inputs
- [x] Tăng password policy
- [x] Đăng ký middleware trong main.py
- [x] Test: API trả 401 khi không có token
- [x] Test: API trả 403 khi role không đủ

## Tiêu chí thành công
- Tất cả endpoints thay đổi dữ liệu trả 401 nếu không có token
- Admin endpoints trả 403 nếu role không phải ADMIN/MANAGER
- Rate limiting hoạt động (login: 5/phút, API: 100/phút)
- Security headers có trong mọi response

## Đánh giá rủi ro
- **Rủi ro**: Frontend không gửi token đúng → kiểm tra AuthContext
- **Giảm thiểu**: Test thủ công với curl trước khi deploy
- **Rủi ro**: Rate limiting block user hợp lệ → set threshold cao (100/phút)

## Bảo mật
- KHÔNG lưu JWT_SECRET_KEY trong code, chỉ dùng env var
- KHÔNG log token/password trong error messages
- Dùng bcrypt (đã có) cho password hashing

## Bước tiếp theo
- Deploy lên Railway để test production
- Monitor logs xem có request bị block không
