-- Migration: Add Subscription Dates
-- Adds trial_ends_at, subscription_starts_at, subscription_ends_at fields
-- to organization_settings for better subscription lifecycle management

-- Add subscription date fields
ALTER TABLE organization_settings
ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS subscription_starts_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS subscription_ends_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS paystack_customer_code VARCHAR(255),
ADD COLUMN IF NOT EXISTS paystack_subscription_code VARCHAR(255),
ADD COLUMN IF NOT EXISTS last_payment_date TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS next_payment_date TIMESTAMPTZ;

-- Create indexes for subscription queries
CREATE INDEX IF NOT EXISTS idx_organization_settings_trial_ends_at 
    ON organization_settings(trial_ends_at) 
    WHERE trial_ends_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_organization_settings_subscription_ends_at 
    ON organization_settings(subscription_ends_at) 
    WHERE subscription_ends_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_organization_settings_status_plan 
    ON organization_settings(status, subscription_plan);

-- Add comments
COMMENT ON COLUMN organization_settings.trial_ends_at IS 'When the free trial period ends';
COMMENT ON COLUMN organization_settings.subscription_starts_at IS 'When the paid subscription started';
COMMENT ON COLUMN organization_settings.subscription_ends_at IS 'When the current subscription period ends';
COMMENT ON COLUMN organization_settings.paystack_customer_code IS 'Paystack customer code for recurring billing';
COMMENT ON COLUMN organization_settings.paystack_subscription_code IS 'Paystack subscription code for recurring billing';
COMMENT ON COLUMN organization_settings.last_payment_date IS 'Date of last successful payment';
COMMENT ON COLUMN organization_settings.next_payment_date IS 'Date of next scheduled payment';

