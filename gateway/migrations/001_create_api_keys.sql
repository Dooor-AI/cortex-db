-- Migration: Create API Keys table
-- Description: Stores API keys for authentication and authorization
-- Created: 2025-01-28

CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Key info (stored as SHA-256 hash)
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    key_prefix VARCHAR(32) NOT NULL,  -- e.g., "cortexdb_admin_abc123"
    
    -- Metadata
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Type and permissions
    type VARCHAR(50) NOT NULL CHECK (type IN ('admin', 'database', 'readonly')),
    permissions JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES api_keys(id) ON DELETE SET NULL,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    enabled BOOLEAN DEFAULT TRUE
);

-- Indexes for performance
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash) WHERE enabled = TRUE;
CREATE INDEX idx_api_keys_type ON api_keys(type);
CREATE INDEX idx_api_keys_created_at ON api_keys(created_at DESC);
CREATE INDEX idx_api_keys_enabled ON api_keys(enabled) WHERE enabled = TRUE;

-- Index for JSONB permissions queries
CREATE INDEX idx_api_keys_permissions ON api_keys USING gin(permissions);

-- Comments for documentation
COMMENT ON TABLE api_keys IS 'API keys for authentication and authorization';
COMMENT ON COLUMN api_keys.key_hash IS 'SHA-256 hash of the actual API key';
COMMENT ON COLUMN api_keys.key_prefix IS 'First ~20 chars of key for display (e.g., cortexdb_admin_abc123...)';
COMMENT ON COLUMN api_keys.type IS 'Type of key: admin, database, or readonly';
COMMENT ON COLUMN api_keys.permissions IS 'JSON permissions: {"databases": ["default"], "readonly": false, "admin": true}';
COMMENT ON COLUMN api_keys.created_by IS 'ID of the API key that created this key (for audit trail)';

