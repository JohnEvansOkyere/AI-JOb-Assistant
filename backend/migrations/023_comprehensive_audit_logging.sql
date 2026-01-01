-- Migration: Comprehensive Audit Logging
-- Adds audit_logs table for tracking all user actions for compliance

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- User who performed the action
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    
    -- Action details
    action_type VARCHAR(50) NOT NULL,  -- 'view', 'create', 'update', 'delete', 'status_change', 'ai_override', 'download'
    resource_type VARCHAR(50) NOT NULL,  -- 'candidate', 'interview', 'report', 'ticket', 'application', 'document'
    resource_id TEXT NOT NULL,  -- ID of the resource
    
    -- Description and metadata
    description TEXT NOT NULL,  -- Human-readable description
    metadata JSONB,  -- Additional context (old_values, new_values, reason, etc.)
    
    -- Request metadata (for security/forensics)
    ip_address TEXT,
    user_agent TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_resource ON audit_logs(user_id, resource_type, resource_id);
-- Note: Date-based index removed - can query by date range using created_at index instead
-- If needed for date-only queries, use: CREATE INDEX idx_audit_logs_date ON audit_logs((created_at::date));

-- Enable RLS
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can view their own logs, admins can view all
CREATE POLICY "Users can view their own audit logs" ON audit_logs
    FOR SELECT TO authenticated USING (
        user_id = (SELECT auth.uid())
    );

CREATE POLICY "Admins can view all audit logs" ON audit_logs
    FOR SELECT TO authenticated USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.id = (SELECT auth.uid())
            AND users.is_admin = TRUE
        )
    );

-- Service role can insert (backend logging)
CREATE POLICY "Service can insert audit logs" ON audit_logs
    FOR INSERT TO service_role WITH CHECK (true);

-- Comments for documentation
COMMENT ON TABLE audit_logs IS 'Comprehensive audit log of all user actions for compliance and tracking';
COMMENT ON COLUMN audit_logs.action_type IS 'Type of action: view, create, update, delete, status_change, ai_override, download';
COMMENT ON COLUMN audit_logs.resource_type IS 'Type of resource: candidate, interview, report, ticket, application, document';
COMMENT ON COLUMN audit_logs.metadata IS 'Additional context stored as JSON (old_values, new_values, reason, etc.)';

