-- Migration: User Authentication and Audit System
-- Date: 2026-02-04
-- Description: Add auth fields to users, creator tracking to jobs, and activity logs table

-- =============================================================================
-- 1. EXTEND USERS TABLE
-- =============================================================================

-- Add email column
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(200) UNIQUE;

-- Add password_hash column
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

-- Add timestamps
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;

-- Add created_by reference
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(user_id);

-- =============================================================================
-- 2. ADD CREATOR TRACKING TO JOBS
-- =============================================================================

-- Add created_by column to track who created the job
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(user_id);

-- Add updated_by column to track last modifier
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS updated_by INTEGER REFERENCES users(user_id);

-- =============================================================================
-- 3. CREATE ACTIVITY LOGS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS activity_logs (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    action_type VARCHAR(50) NOT NULL,      -- LOGIN, LOGOUT, CREATE, UPDATE, DELETE
    entity_type VARCHAR(50),                -- JOB, USER, CUSTOMER, VENDOR, SERVICE
    entity_id INTEGER,
    entity_ref VARCHAR(100),                -- job_no, user_code, etc. for display
    old_value JSONB,
    new_value JSONB,
    description TEXT,                       -- Human-readable description
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_entity ON activity_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_action ON activity_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_activity_logs_created ON activity_logs(created_at DESC);

-- =============================================================================
-- 4. CREATE DEFAULT ADMIN USER
-- =============================================================================

-- Insert admin user if not exists (password will be set via Python security module)
-- Default password: Admin@123 (must be changed on first login)
INSERT INTO users (user_code, full_name, email, role, is_active)
VALUES ('ADMIN', 'System Administrator', 'admin@5pvietnam.com', 'ADMIN', TRUE)
ON CONFLICT (user_code) DO UPDATE SET
    email = EXCLUDED.email,
    role = EXCLUDED.role;

-- =============================================================================
-- 5. CREATE ROLE TYPE FOR CONSISTENCY
-- =============================================================================

-- Create enum type for roles (optional, for stricter validation)
DO $$ BEGIN
    CREATE TYPE user_role AS ENUM ('ADMIN', 'MANAGER', 'STAFF');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Note: Keep role as VARCHAR for flexibility, enum is optional

-- =============================================================================
-- 6. UPDATE TRIGGER FOR UPDATED_AT
-- =============================================================================

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VERIFICATION QUERIES (run to check migration success)
-- =============================================================================

-- Check users table structure:
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users';

-- Check activity_logs table:
-- SELECT * FROM activity_logs LIMIT 5;

-- Check admin user:
-- SELECT user_id, user_code, email, role FROM users WHERE user_code = 'ADMIN';
