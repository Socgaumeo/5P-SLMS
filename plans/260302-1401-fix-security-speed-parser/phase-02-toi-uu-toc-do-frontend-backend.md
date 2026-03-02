# Phase 2: Tối ưu Tốc độ Frontend & Backend

## Context Links
- [Plan tổng](plan.md)
- [Báo cáo speed optimization](../reports/research-260302-1112-speed-optimization.md)
- [vite.config.js](../../frontend/vite.config.js) — Hiện tại rất tối giản
- [main.jsx](../../frontend/src/main.jsx) — Entry point React

## Tổng quan
- **Ngày**: 2026-03-02
- **Ưu tiên**: P1
- **Trạng thái**: completed
- **Mô tả**: Cài Vercel Speed Insights, tối ưu Vite build, thêm gzip compression cho backend

## Phát hiện quan trọng

1. Frontend chỉ có React + Vite minimal config — chưa code splitting, chưa lazy loading
2. Vercel Speed Insights dùng `@vercel/speed-insights/react` (KHÔNG phải `/next`)
3. Backend chưa có response compression (gzip/brotli)
4. package.json chỉ có 2 dependencies (react, react-dom) — bundle nhỏ, ít cần tối ưu phức tạp
5. App là SPA đơn trang (App.jsx) — KHÔNG cần React Router lazy loading

## Yêu cầu

### Chức năng
- Vercel Speed Insights hoạt động và báo cáo Web Vitals
- Bundle size giảm nhờ manual chunks
- API response nén gzip

### Phi chức năng
- FCP < 1.5s (hiện ~2.5s)
- Bundle < 500KB (kiểm tra sau build)
- API response size giảm ~60% nhờ gzip

## File liên quan

| File | Hành động | Mô tả |
|------|-----------|-------|
| `frontend/package.json` | **SỬA** | Thêm `@vercel/speed-insights` dependency |
| `frontend/src/main.jsx` | **SỬA** | Thêm `<SpeedInsights />` component |
| `frontend/vite.config.js` | **SỬA** | Thêm manual chunks, build optimization |
| `backend/main.py` | **SỬA** | Thêm GZipMiddleware |
| `backend/requirements.txt` | **SỬA** | (không cần thêm — uvicorn đã có starlette) |

## Các bước thực hiện

### Bước 1: Cài Vercel Speed Insights

```bash
cd frontend && npm install @vercel/speed-insights
```

Sửa `frontend/src/main.jsx`:
```jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { SpeedInsights } from '@vercel/speed-insights/react'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
    <SpeedInsights />
  </StrictMode>,
)
```

### Bước 2: Tối ưu Vite build config

Sửa `frontend/vite.config.js`:
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
        },
      },
    },
    // Giới hạn cảnh báo chunk size
    chunkSizeWarningLimit: 500,
  },
})
```

### Bước 3: Thêm GZip compression cho backend

Sửa `backend/main.py` — thêm sau CORS middleware:
```python
from starlette.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=500)
```

GZipMiddleware có sẵn trong starlette (đã cài cùng FastAPI), KHÔNG cần thêm package.

### Bước 4: Kiểm tra bundle size

```bash
cd frontend && npm run build
# Kiểm tra output trong dist/assets/
# Mục tiêu: vendor-react chunk < 150KB, main chunk < 300KB
```

## Checklist
- [x] Cài `@vercel/speed-insights` trong frontend
- [x] Thêm `<SpeedInsights />` vào main.jsx
- [x] Cấu hình manual chunks trong vite.config.js
- [x] Thêm GZipMiddleware vào backend main.py
- [x] Build frontend và kiểm tra bundle size
- [x] Deploy và kiểm tra Speed Insights trên Vercel dashboard

## Tiêu chí thành công
- Vercel Speed Insights hiện dữ liệu Web Vitals trên dashboard
- `npm run build` thành công, bundle < 500KB tổng
- API response có header `Content-Encoding: gzip`

## Đánh giá rủi ro
- **Thấp**: Vercel Speed Insights chỉ là monitoring, không ảnh hưởng chức năng
- **Thấp**: GZipMiddleware đã được test rộng rãi trong starlette
- **Trung bình**: Manual chunks có thể gây lỗi nếu import sai — kiểm tra build

## Bước tiếp theo
- Sau deploy, theo dõi Web Vitals 1 tuần trên Vercel dashboard
- Nếu latency API vẫn cao (>300ms), cân nhắc Cloudflare CDN miễn phí
