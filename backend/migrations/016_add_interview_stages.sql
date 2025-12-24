-- Migration: Multi-Stage Interview System
-- Adds support for configurable interview stages per job
-- Created: 2025-12-24

-- ============================================================================
-- JOB INTERVIEW STAGES TABLE
-- Defines interview stages for each job (configured by recruiter)
-- ============================================================================

CREATE TABLE IF NOT EXISTS job_interview_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE,
    
    -- Stage Configuration
    stage_number INTEGER NOT NULL,  -- 1, 2, 3, etc.
    stage_name VARCHAR(255) NOT NULL,  -- "Phone Screen", "Technical", "Final Interview"
    stage_type VARCHAR(50) NOT NULL DEFAULT 'calendar',  -- 'ai' or 'calendar' (human interview)
    is_required BOOLEAN DEFAULT true,  -- Whether this stage must be completed
    
    -- Ordering
    order_index INTEGER NOT NULL,  -- For sorting stages (1, 2, 3, etc.)
    
    -- Locking (prevents accidental changes during active hiring)
    is_locked BOOLEAN DEFAULT false,  -- true once first interview starts
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT unique_job_stage_number UNIQUE (job_id, stage_number),
    CONSTRAINT valid_stage_type CHECK (stage_type IN ('ai', 'calendar')),
    CONSTRAINT positive_stage_number CHECK (stage_number > 0),
    CONSTRAINT positive_order_index CHECK (order_index > 0)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_job_interview_stages_job ON job_interview_stages(job_id);
CREATE INDEX IF NOT EXISTS idx_job_interview_stages_order ON job_interview_stages(job_id, order_index);

-- Add comment
COMMENT ON TABLE job_interview_stages IS 'Defines interview stages for each job. Each job can have 1-N stages. Only one stage per job can be type "ai".';
COMMENT ON COLUMN job_interview_stages.stage_type IS 'Type of interview: "ai" for AI-powered voice interview, "calendar" for human/calendar-based interview';

-- ============================================================================
-- CANDIDATE INTERVIEW PROGRESS TABLE
-- Tracks candidate progression through interview stages
-- ============================================================================

CREATE TABLE IF NOT EXISTS candidate_interview_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_id UUID NOT NULL REFERENCES job_descriptions(id) ON DELETE CASCADE,
    
    -- Current Status
    current_stage_number INTEGER,  -- NULL if not started, otherwise references job_interview_stages.stage_number
    status VARCHAR(50) NOT NULL DEFAULT 'not_started',  -- not_started, in_progress, completed, rejected, offer
    
    -- Stage Tracking
    completed_stages JSONB DEFAULT '[]'::jsonb,  -- Array of completed stage numbers: [1, 2]
    skipped_stages JSONB DEFAULT '[]'::jsonb,  -- Array of skipped stage numbers: [3]
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT unique_candidate_job_progress UNIQUE (candidate_id, job_id),
    CONSTRAINT valid_progress_status CHECK (status IN ('not_started', 'in_progress', 'completed', 'rejected', 'offer', 'accepted'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_candidate_progress_candidate ON candidate_interview_progress(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_progress_job ON candidate_interview_progress(job_id);
CREATE INDEX IF NOT EXISTS idx_candidate_progress_status ON candidate_interview_progress(status);
CREATE INDEX IF NOT EXISTS idx_candidate_progress_current_stage ON candidate_interview_progress(job_id, current_stage_number);

-- Add comment
COMMENT ON TABLE candidate_interview_progress IS 'Tracks candidate progression through interview stages for each job';
COMMENT ON COLUMN candidate_interview_progress.completed_stages IS 'JSON array of stage numbers that have been completed: [1, 2]';
COMMENT ON COLUMN candidate_interview_progress.skipped_stages IS 'JSON array of stage numbers that were skipped: [3]';

-- ============================================================================
-- ADD STAGE NUMBER TO EXISTING TABLES
-- ============================================================================

-- Add stage_number to interviews table (links AI interviews to stages)
ALTER TABLE interviews 
ADD COLUMN IF NOT EXISTS stage_number INTEGER;

-- Add comment
COMMENT ON COLUMN interviews.stage_number IS 'References job_interview_stages.stage_number for this job. NULL for legacy interviews.';

-- Add stage_number to calendar_events table (links calendar events to stages)
ALTER TABLE calendar_events 
ADD COLUMN IF NOT EXISTS stage_number INTEGER;

-- Add comment
COMMENT ON COLUMN calendar_events.stage_number IS 'References job_interview_stages.stage_number for this job. NULL for legacy events.';

-- ============================================================================
-- FUNCTION: Enforce single AI stage per job
-- ============================================================================

CREATE OR REPLACE FUNCTION check_single_ai_stage_per_job()
RETURNS TRIGGER AS $$
BEGIN
    -- Only check if this is an AI stage
    IF NEW.stage_type = 'ai' THEN
        -- Check if another AI stage exists for this job
        IF EXISTS (
            SELECT 1 FROM job_interview_stages 
            WHERE job_id = NEW.job_id 
            AND stage_type = 'ai' 
            AND id != COALESCE(NEW.id, '00000000-0000-0000-0000-000000000000'::uuid)
        ) THEN
            RAISE EXCEPTION 'Only one AI interview stage is allowed per job';
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
DROP TRIGGER IF EXISTS enforce_single_ai_stage ON job_interview_stages;
CREATE TRIGGER enforce_single_ai_stage
    BEFORE INSERT OR UPDATE ON job_interview_stages
    FOR EACH ROW
    EXECUTE FUNCTION check_single_ai_stage_per_job();

-- ============================================================================
-- FUNCTION: Auto-create default stages for existing jobs (optional)
-- Creates a default 1-stage (AI) interview process for jobs without stages
-- ============================================================================

CREATE OR REPLACE FUNCTION create_default_stages_for_job(p_job_id UUID)
RETURNS void AS $$
DECLARE
    stage_count INTEGER;
BEGIN
    -- Check if job already has stages
    SELECT COUNT(*) INTO stage_count
    FROM job_interview_stages
    WHERE job_id = p_job_id;
    
    -- If no stages exist, create default 1-stage (AI) process
    IF stage_count = 0 THEN
        INSERT INTO job_interview_stages (job_id, stage_number, stage_name, stage_type, is_required, order_index)
        VALUES (p_job_id, 1, 'AI Interview', 'ai', true, 1);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Add comment
COMMENT ON FUNCTION create_default_stages_for_job IS 'Creates default 1-stage (AI) interview process for a job if none exist';

