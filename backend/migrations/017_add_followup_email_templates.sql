-- Migration: Add Follow-Up Email Template Types
-- Adds reassurance_14day and auto_timeout_rejection template types
-- Created: 2025-12-26

-- ============================================================================
-- EMAIL TEMPLATES: Add follow-up email template types
-- ============================================================================

-- Drop existing constraint
ALTER TABLE email_templates 
DROP CONSTRAINT IF EXISTS valid_template_type;

-- Recreate constraint with new follow-up template types included
ALTER TABLE email_templates 
ADD CONSTRAINT valid_template_type 
CHECK (template_type IN (
    'interview_invitation', 
    'acceptance', 
    'rejection', 
    'cv_rejection',
    'interview_rejection',
    'offer_letter', 
    'application_received',
    'reassurance_14day',        -- 14-day reassurance email
    'auto_timeout_rejection',   -- 30-day auto-rejection email
    'custom'
));

-- Add comment
COMMENT ON COLUMN email_templates.template_type IS 'Template type: interview_invitation, acceptance, rejection, cv_rejection, interview_rejection, offer_letter, application_received, reassurance_14day, auto_timeout_rejection, or custom';

