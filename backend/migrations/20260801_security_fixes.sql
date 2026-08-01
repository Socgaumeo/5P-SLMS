-- 2026-08-01 Security fixes (Sen)
-- 1) Bảng token reset mật khẩu (forgot-password flow)
CREATE TABLE IF NOT EXISTS public.password_resets (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES public.users(user_id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    request_ip TEXT
);
CREATE INDEX IF NOT EXISTS idx_password_resets_token ON public.password_resets(token_hash);
CREATE INDEX IF NOT EXISTS idx_password_resets_user  ON public.password_resets(user_id);
ALTER TABLE public.password_resets ENABLE ROW LEVEL SECURITY;

-- 2) Bật RLS cho 8 bảng public đang tắt (lint: rls_disabled_in_public)
--    Không tạo policy => anon/authenticated bị chặn; backend dùng service_role vẫn bypass.
ALTER TABLE public.audit_logs           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.automation_logs      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.customer_surcharges  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.employees            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.message_templates    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rate_file_references ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.services             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.vendor_surcharges    ENABLE ROW LEVEL SECURITY;

-- Ghi chú: activity_logs đã có sẵn cột user_agent (dùng cho ghi nhận thiết bị login).
