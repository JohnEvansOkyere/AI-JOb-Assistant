-- Migration: Add application_received template type
-- Adds 'application_received' to the allowed template types for email templates

-- Drop existing constraint
ALTER TABLE email_templates 
DROP CONSTRAINT IF EXISTS valid_template_type;

-- Recreate constraint with application_received included
ALTER TABLE email_templates 
ADD CONSTRAINT valid_template_type 
CHECK (template_type IN ('interview_invitation', 'acceptance', 'rejection', 'offer_letter', 'application_received', 'custom'));

