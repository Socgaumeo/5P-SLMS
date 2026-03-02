---
title: "Fix Bảo mật, Tốc độ & Parser Báo giá"
description: "Sửa lỗ hổng bảo mật critical, tối ưu tốc độ, cải thiện parser đọc file báo giá"
status: completed
priority: P1
effort: 6h
branch: main
tags: [security, performance, parser, production]
created: 2026-03-02
---

# Kế hoạch: Fix Bảo mật, Tốc độ & Parser Báo giá

## Tổng quan

Dự án 5P-SLMS đã deploy trên Railway + Vercel. Phát hiện 3 vấn đề cần fix:

1. **Bảo mật** (CRITICAL) — Admin/job endpoints không có authentication
2. **Tốc độ** — Chưa tối ưu bundle, chưa có monitoring
3. **Parser báo giá** — Regex đọc thiếu không phát hiện được, bỏ qua ghi chú/phụ phí

## Kiến trúc hiện tại

```
[5pvietnam.com] → Vercel → React SPA (VITE_API_URL)
[api.5pvietnam.com] → Railway → FastAPI (gunicorn+uvicorn)
                                    ↓
                        Supabase PostgreSQL (Singapore)
```

## Các Phase

| # | Phase | Ưu tiên | Thời gian | Trạng thái | File |
|---|-------|---------|-----------|------------|------|
| 1 | Bảo mật Backend | P0-CRITICAL | 2h | completed | [phase-01](phase-01-bao-mat-backend.md) |
| 2 | Tối ưu Tốc độ | P1 | 2h | completed | [phase-02](phase-02-toi-uu-toc-do-frontend-backend.md) |
| 3 | Cải thiện Parser Báo giá | P1 | 2h | completed | [phase-03](phase-03-cai-thien-parser-doc-file-bao-gia.md) |

## Thứ tự thực hiện

- Phase 1 và Phase 2 có thể chạy **song song** (backend vs frontend)
- Phase 3 chạy sau Phase 1 (cùng sửa backend)

## Rủi ro chính

- Phase 1: Frontend đang gọi API không có token → cần kiểm tra AuthContext gửi token đúng
- Phase 2: Vercel Speed Insights cần deploy mới để test
- Phase 3: AI fallback tốn thêm $0.004/file nhưng tăng chính xác đáng kể
