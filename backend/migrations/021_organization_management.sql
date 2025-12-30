-- Migration: Organization Management
-- Adds subscription plans, usage limits, and organization status tracking

-- Organization subscription plans
CREATE TYPE subscription_plan AS ENUM ('free', 'starter', 'professional', 'enterprise', 'custom');

-- Organization status
CREATE TYPE organization_status AS ENUM ('active', 'paused', 'suspended', 'trial');

-- Create organization_settings table (one per company_name)
CREATE TABLE IF NOT EXISTS organization_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name TEXT NOT NULL UNIQUE,  -- Links to users.company_name
    
    -- Subscription & Billing
    subscription_plan subscription_plan DEFAULT 'free',
    status organization_status DEFAULT 'active',
    billing_email TEXT,
    
    -- Usage Limits (NULL means unlimited)
    monthly_interview_limit INTEGER,  -- Max interviews per month
    monthly_cost_limit_usd DECIMAL(10, 2),  -- Max monthly AI cost in USD
    daily_cost_limit_usd DECIMAL(10, 2),  -- Max daily AI cost in USD
    
    -- Admin Notes
    admin_notes TEXT,  -- Internal notes about the organization
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    
    CONSTRAINT valid_limits CHECK (
        (monthly_interview_limit IS NULL OR monthly_interview_limit > 0) AND
        (monthly_cost_limit_usd IS NULL OR monthly_cost_limit_usd > 0) AND
        (daily_cost_limit_usd IS NULL OR daily_cost_limit_usd > 0)
    )
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_organization_settings_company_name ON organization_settings(company_name);
CREATE INDEX IF NOT EXISTS idx_organization_settings_status ON organization_settings(status);
CREATE INDEX IF NOT EXISTS idx_organization_settings_subscription_plan ON organization_settings(subscription_plan);

-- Admin action logs (audit trail)
CREATE TABLE IF NOT EXISTS admin_action_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    admin_user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    
    -- Action details
    action_type VARCHAR(100) NOT NULL,  -- e.g., 'update_organization_status', 'change_subscription_plan', 'set_usage_limit'
    target_type VARCHAR(50) NOT NULL,  -- 'organization', 'user', 'system'
    target_id TEXT NOT NULL,  -- ID of the target (company_name for orgs, user_id for users)
    
    -- Changes
    old_values JSONB,  -- Previous values
    new_values JSONB,  -- New values
    description TEXT,  -- Human-readable description
    
    -- Metadata
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Create indexes for admin logs
CREATE INDEX IF NOT EXISTS idx_admin_action_logs_admin_user_id ON admin_action_logs(admin_user_id);
CREATE INDEX IF NOT EXISTS idx_admin_action_logs_target ON admin_action_logs(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_admin_action_logs_action_type ON admin_action_logs(action_type);
CREATE INDEX IF NOT EXISTS idx_admin_action_logs_created_at ON admin_action_logs(created_at DESC);

-- Enable RLS
ALTER TABLE organization_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_action_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Only admins can view/edit organization settings
CREATE POLICY "Admins can view organization settings" ON organization_settings
    FOR SELECT TO authenticated USING (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND is_admin = TRUE)
    );

CREATE POLICY "Admins can insert organization settings" ON organization_settings
    FOR INSERT TO authenticated WITH CHECK (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND is_admin = TRUE)
    );

CREATE POLICY "Admins can update organization settings" ON organization_settings
    FOR UPDATE TO authenticated USING (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND is_admin = TRUE)
    );

-- RLS Policies: Only admins can view admin action logs
CREATE POLICY "Admins can view admin action logs" ON admin_action_logs
    FOR SELECT TO authenticated USING (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND is_admin = TRUE)
    );

CREATE POLICY "Admins can insert admin action logs" ON admin_action_logs
    FOR INSERT TO authenticated WITH CHECK (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND is_admin = TRUE)
    );

-- Add comments
COMMENT ON TABLE organization_settings IS 'Organization-level settings including subscription plans, usage limits, and status';
COMMENT ON TABLE admin_action_logs IS 'Audit log of all admin actions for compliance and debugging';

COMMENT ON COLUMN organization_settings.subscription_plan IS 'Subscription tier: free, starter, professional, enterprise, custom';
COMMENT ON COLUMN organization_settings.status IS 'Organization status: active, paused, suspended, trial';
COMMENT ON COLUMN organization_settings.monthly_interview_limit IS 'Maximum interviews per month (NULL = unlimited)';
COMMENT ON COLUMN organization_settings.monthly_cost_limit_usd IS 'Maximum monthly AI cost in USD (NULL = unlimited)';
COMMENT ON COLUMN organization_settings.daily_cost_limit_usd IS 'Maximum daily AI cost in USD (NULL = unlimited)';

