-- Migration: Add is_default field to email_templates
-- Allows marking templates as default for prioritization
-- Created: 2025-12-24

-- Add is_default column to email_templates
ALTER TABLE email_templates 
ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT false;

-- Create index for default template lookups
CREATE INDEX IF NOT EXISTS idx_email_templates_is_default ON email_templates(recruiter_id, template_type, is_default);

-- Add comment
COMMENT ON COLUMN email_templates.is_default IS 'If true, this template is marked as default and will be prioritized when looking up templates by type';

