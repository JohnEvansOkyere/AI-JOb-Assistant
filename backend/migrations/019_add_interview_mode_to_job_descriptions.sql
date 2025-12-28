-- Migration: Add interview_mode to job_descriptions table
-- This allows recruiters to set the interview mode (text or voice) at the job level
-- All tickets created for this job will inherit this mode

-- Add interview_mode column to job_descriptions
ALTER TABLE job_descriptions
ADD COLUMN IF NOT EXISTS interview_mode TEXT NOT NULL DEFAULT 'text'
CHECK (interview_mode IN ('text', 'voice'));

-- Create index for filtering
CREATE INDEX IF NOT EXISTS idx_job_descriptions_interview_mode
ON job_descriptions(interview_mode);

-- Add comment
COMMENT ON COLUMN job_descriptions.interview_mode IS 'Interview mode for this job: "text" for text-based interviews (typing) or "voice" for voice-based interviews (speaking). All tickets created for this job will inherit this mode.';

-- Update existing jobs to have 'text' mode (backward compatibility)
UPDATE job_descriptions 
SET interview_mode = 'text' 
WHERE interview_mode IS NULL;

