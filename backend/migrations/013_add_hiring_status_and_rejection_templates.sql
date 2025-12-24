-- Migration: Add Hiring Status and Rejection Email Template Types
-- Adds hiring_status field to job_descriptions and new rejection template types
-- Created: 2025-12-24

-- ============================================================================
-- JOB DESCRIPTIONS: Add hiring_status field
-- ============================================================================

-- Add hiring_status column to job_descriptions
ALTER TABLE job_descriptions 
ADD COLUMN IF NOT EXISTS hiring_status VARCHAR(50) DEFAULT 'active';

-- Add constraint for valid hiring_status values
ALTER TABLE job_descriptions 
DROP CONSTRAINT IF EXISTS valid_hiring_status;

ALTER TABLE job_descriptions 
ADD CONSTRAINT valid_hiring_status 
CHECK (hiring_status IN ('active', 'screening', 'interviewing', 'filled', 'closed'));

-- Create index for hiring_status lookups
CREATE INDEX IF NOT EXISTS idx_job_descriptions_hiring_status ON job_descriptions(hiring_status);

-- Update existing jobs to have appropriate status based on is_active
UPDATE job_descriptions 
SET hiring_status = CASE 
    WHEN is_active = true THEN 'active'
    ELSE 'closed'
END
WHERE hiring_status = 'active' OR hiring_status IS NULL;

-- Add comment
COMMENT ON COLUMN job_descriptions.hiring_status IS 'Recruitment lifecycle status: active (accepting applications), screening, interviewing, filled (position filled), closed (no longer hiring)';

-- ============================================================================
-- EMAIL TEMPLATES: Add rejection template types
-- ============================================================================

-- Drop existing constraint
ALTER TABLE email_templates 
DROP CONSTRAINT IF EXISTS valid_template_type;

-- Recreate constraint with cv_rejection and interview_rejection included
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
    'custom'
));

