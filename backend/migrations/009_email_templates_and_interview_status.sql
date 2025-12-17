-- Migration: Email Templates and Interview Job Status
-- Adds job_status to interviews and enhances email templates

-- Add job_status column to interviews table
ALTER TABLE interviews 
ADD COLUMN IF NOT EXISTS job_status VARCHAR(50) DEFAULT NULL;

-- Add constraint for valid job_status values
ALTER TABLE interviews 
ADD CONSTRAINT IF NOT EXISTS valid_job_status 
CHECK (job_status IS NULL OR job_status IN ('accepted', 'rejected', 'under_review', 'pending'));

-- Create index for filtering by job_status
CREATE INDEX IF NOT EXISTS idx_interviews_job_status ON interviews(job_status);
CREATE INDEX IF NOT EXISTS idx_interviews_job_description_status ON interviews(job_description_id, job_status);

-- Update email_templates table to support template types
ALTER TABLE email_templates 
ADD COLUMN IF NOT EXISTS template_type VARCHAR(50) DEFAULT 'custom';

-- Add constraint for valid template types
ALTER TABLE email_templates 
ADD CONSTRAINT IF NOT EXISTS valid_template_type 
CHECK (template_type IN ('interview_invitation', 'acceptance', 'rejection', 'offer_letter', 'custom'));

-- Add template variables documentation column
ALTER TABLE email_templates 
ADD COLUMN IF NOT EXISTS available_variables TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Create index for template type lookups
CREATE INDEX IF NOT EXISTS idx_email_templates_type ON email_templates(recruiter_id, template_type);

-- Add comment explaining template variables
COMMENT ON COLUMN email_templates.available_variables IS 'List of available variables for this template (e.g., {{first_name}}, {{job_title}}, {{salary}})';

