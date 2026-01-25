-- =============================================================================
-- TẠO LẠI BẢNG VENDOR_SURCHARGES VỚI CẤU TRÚC ĐÚNG
-- =============================================================================

-- Xóa bảng phụ thuộc trước (nếu có)
DROP TABLE IF EXISTS public.vendor_surcharge_prices CASCADE;

-- Xóa bảng vendor_surcharges cũ nếu tồn tại
DROP TABLE IF EXISTS public.vendor_surcharges CASCADE;

-- Tạo lại bảng vendor_surcharges với cấu trúc đúng
CREATE TABLE public.vendor_surcharges (
    id SERIAL PRIMARY KEY,
    vendor_id INTEGER NOT NULL REFERENCES vendors(vendor_id) ON DELETE CASCADE,
    surcharge_code VARCHAR(50) NOT NULL,
    description TEXT,
    amount DECIMAL(18,2),
    unit VARCHAR(20),
    conditions TEXT,
    effective_date DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index
CREATE INDEX idx_vendor_surcharges_vendor_id ON public.vendor_surcharges(vendor_id);
CREATE INDEX idx_vendor_surcharges_surcharge_code ON public.vendor_surcharges(surcharge_code);

-- Comment
COMMENT ON TABLE public.vendor_surcharges IS 'Bảng phụ phí của nhà vận chuyển';
