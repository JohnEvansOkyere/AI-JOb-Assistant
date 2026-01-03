-- ============================================================================
-- Migration: Add Email Verification Fields
-- Adds email verification code and status to users table
-- ============================================================================

-- Add email verification fields to users table
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS email_verification_code VARCHAR(6),
ADD COLUMN IF NOT EXISTS email_verification_code_expires_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS email_verification_attempts INTEGER DEFAULT 0;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email_verification_code 
ON public.users(email_verification_code) 
WHERE email_verification_code IS NOT NULL;

-- Create index for email verification status
CREATE INDEX IF NOT EXISTS idx_users_email_verified 
ON public.users(email_verified_at) 
WHERE email_verified_at IS NULL;

-- Add comment for documentation
COMMENT ON COLUMN public.users.email_verification_code IS '6-digit verification code sent via email';
COMMENT ON COLUMN public.users.email_verification_code_expires_at IS 'Expiration timestamp for verification code (typically 10 minutes)';
COMMENT ON COLUMN public.users.email_verified_at IS 'Timestamp when email was verified (NULL if not verified)';
COMMENT ON COLUMN public.users.email_verification_attempts IS 'Number of failed verification attempts (for rate limiting)';

