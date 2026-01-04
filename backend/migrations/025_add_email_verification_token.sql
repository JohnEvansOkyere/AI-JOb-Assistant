-- ============================================================================
-- Migration: Add Email Verification Token Columns
-- Adds token-based verification support (for button/link verification)
-- Note: This assumes email_verification_code already exists
-- ============================================================================

-- Add token-based verification columns
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS email_verification_token TEXT,
ADD COLUMN IF NOT EXISTS email_verification_token_expires_at TIMESTAMPTZ;

-- Create index for faster token lookups
CREATE INDEX IF NOT EXISTS idx_users_email_verification_token 
ON public.users(email_verification_token) 
WHERE email_verification_token IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN public.users.email_verification_token IS 'Secure token for link-based email verification';
COMMENT ON COLUMN public.users.email_verification_token_expires_at IS 'Expiration timestamp for verification token (typically 10 minutes)';

