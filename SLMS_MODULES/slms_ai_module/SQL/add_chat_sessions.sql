-- ============================================
-- SLMS Chat Sessions Migration
-- For Conversation Memory (Phase 3)
-- ============================================

-- Chat Sessions table (for conversation context)
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(user_id),
    
    -- Session state
    last_intent VARCHAR(50),
    collected_entities JSONB DEFAULT '{}',
    pending_action JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP DEFAULT NOW() + INTERVAL '30 minutes'
);

-- Chat Messages table (for history)
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    
    -- Message content
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    
    -- AI processing results
    intent VARCHAR(50),
    confidence DECIMAL(3,2),
    entities JSONB,
    
    -- Metadata
    input_type VARCHAR(20) DEFAULT 'text', -- text, image, excel, pdf
    processing_time_ms INTEGER,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

-- Generated Messages table (for copy to Zalo)
CREATE TABLE IF NOT EXISTS generated_messages (
    gen_message_id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(session_id),
    job_id INTEGER REFERENCES jobs(job_id),
    
    -- Message
    message_type VARCHAR(50) NOT NULL, -- VENDOR_REQUEST, CUSTOMER_CONFIRM, etc.
    template_code VARCHAR(50),
    content TEXT NOT NULL,
    
    -- Status
    is_copied BOOLEAN DEFAULT FALSE,
    copied_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_expires ON chat_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_generated_messages_job ON generated_messages(job_id);

-- Function to update session timestamp
CREATE OR REPLACE FUNCTION update_chat_session_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.expires_at = NOW() + INTERVAL '30 minutes';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger
DROP TRIGGER IF EXISTS trigger_update_chat_session ON chat_sessions;
CREATE TRIGGER trigger_update_chat_session
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_chat_session_timestamp();

-- Cleanup expired sessions (run periodically)
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM chat_sessions WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Usage: SELECT cleanup_expired_sessions();

-- ============================================
-- SAMPLE DATA FOR TESTING
-- ============================================

-- Insert test session (optional)
-- INSERT INTO chat_sessions (user_id, last_intent, collected_entities)
-- VALUES (1, 'create_booking', '{"customer_code": "DRT1"}');
