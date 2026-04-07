-- ============================================================
-- Migration 003: Documents & Debit Templates
-- Created: 2026-04-06
-- Purpose: Document management (Telegram Bot capture + cloud backup)
--          + Debit note template engine
-- ============================================================

-- 1. Documents table — chứng từ gắn với jobs
-- Primary storage: Telegram file_id (free, permanent)
-- Backup: OneDrive / Google Drive (optional)
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id INTEGER REFERENCES jobs(job_id) ON DELETE CASCADE,
  doc_type TEXT NOT NULL CHECK (doc_type IN (
    'AN', 'DEBIT', 'DO', 'CD', 'CO', 'INVOICE', 'AWB', 'BL', 'PACKING_LIST', 'OTHER'
  )),
  file_name TEXT NOT NULL,
  file_size INTEGER,
  mime_type TEXT,

  -- Multi-tier storage
  storage_type TEXT NOT NULL DEFAULT 'telegram'
    CHECK (storage_type IN ('telegram', 'gdrive', 'onedrive', 'web_upload', 'external_link')),
  telegram_file_id TEXT,
  telegram_message_id INTEGER,
  telegram_chat_id TEXT,
  external_url TEXT,
  cloud_backup_path TEXT,
  cloud_backup_status TEXT DEFAULT 'pending'
    CHECK (cloud_backup_status IN ('pending', 'synced', 'failed', 'skipped')),

  -- Audit
  uploaded_by INTEGER REFERENCES users(user_id),
  uploaded_by_telegram TEXT,
  uploaded_at TIMESTAMPTZ DEFAULT NOW(),
  notes TEXT,
  metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_documents_job_id ON documents(job_id);
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_storage_type ON documents(storage_type);
CREATE INDEX IF NOT EXISTS idx_documents_cloud_backup_status ON documents(cloud_backup_status);

-- 2. Debit templates table — Excel templates per customer
CREATE TABLE IF NOT EXISTS debit_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id INTEGER REFERENCES customers(customer_id),
  template_name TEXT NOT NULL,
  telegram_file_id TEXT,
  local_file_path TEXT,
  field_mapping JSONB NOT NULL,
  sheet_config JSONB DEFAULT '{}',
  is_active BOOLEAN DEFAULT true,
  created_by INTEGER REFERENCES users(user_id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_debit_templates_customer_id ON debit_templates(customer_id);
CREATE INDEX IF NOT EXISTS idx_debit_templates_is_active ON debit_templates(is_active);
