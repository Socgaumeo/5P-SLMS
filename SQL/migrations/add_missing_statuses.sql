-- Add missing status codes to master_statuses
-- This fixes the foreign key constraint error when assigning vehicles

INSERT INTO master_statuses (status_code, name_vi, color_code, is_active) 
VALUES 
    ('DISPATCHED', 'Đã điều xe', '#8B5CF6', TRUE),
    ('IN_TRANSIT', 'Đang vận chuyển', '#F59E0B', TRUE)
ON CONFLICT (status_code) DO NOTHING;

-- Verify the new statuses
SELECT * FROM master_statuses ORDER BY status_code;
