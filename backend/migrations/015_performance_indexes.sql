-- Migration: Performance Optimization Indexes
-- Adds indexes for frequently queried columns to improve query performance
-- Created: 2025-12-24

-- ============================================================================
-- APPLICATIONS TABLE
-- ============================================================================
-- Note: job_applications doesn't have recruiter_id directly
-- Applications are linked to recruiters via job_description_id -> job_descriptions.recruiter_id
-- So indexes are on job_description_id (which is used in joins)

-- Composite index for job + status filtering (common query pattern)
CREATE INDEX IF NOT EXISTS idx_job_applications_job_status 
ON job_applications(job_description_id, status);

-- Composite index for candidate + job (for uniqueness and lookups)
CREATE INDEX IF NOT EXISTS idx_applications_candidate_job 
ON job_applications(candidate_id, job_description_id);

-- Status filtering (already exists but ensuring it's optimized)
CREATE INDEX IF NOT EXISTS idx_applications_status 
ON job_applications(status) 
WHERE status IS NOT NULL;

-- ============================================================================
-- CV DETAILED SCREENING
-- ============================================================================

-- Application lookup (already exists but ensuring it's there)
CREATE INDEX IF NOT EXISTS idx_cv_detailed_screening_application 
ON cv_detailed_screening(application_id);

-- Recommendation filtering
CREATE INDEX IF NOT EXISTS idx_cv_detailed_screening_recommendation 
ON cv_detailed_screening(recommendation);

-- Composite for job match queries
CREATE INDEX IF NOT EXISTS idx_cv_detailed_screening_job_match 
ON cv_detailed_screening(application_id, job_match_score DESC);

-- ============================================================================
-- EMAIL TEMPLATES
-- ============================================================================

-- Composite index for template lookups (already exists but ensuring)
CREATE INDEX IF NOT EXISTS idx_email_templates_recruiter_type 
ON email_templates(recruiter_id, template_type);

-- Default template lookups
CREATE INDEX IF NOT EXISTS idx_email_templates_recruiter_default_type 
ON email_templates(recruiter_id, is_default, template_type);

-- ============================================================================
-- COMPANY BRANDING
-- ============================================================================

-- Default branding lookups
CREATE INDEX IF NOT EXISTS idx_company_branding_recruiter_default 
ON company_branding(recruiter_id, is_default);

-- ============================================================================
-- INTERVIEWS
-- ============================================================================

-- Composite for job + status filtering
CREATE INDEX IF NOT EXISTS idx_interviews_job_status 
ON interviews(job_description_id, job_status) 
WHERE job_status IS NOT NULL;

-- ============================================================================
-- DETAILED INTERVIEW ANALYSIS
-- ============================================================================

-- Interview lookup
CREATE INDEX IF NOT EXISTS idx_interview_analysis_interview 
ON detailed_interview_analysis(interview_id);

-- Recommendation filtering
CREATE INDEX IF NOT EXISTS idx_interview_analysis_recommendation 
ON detailed_interview_analysis(recommendation);

-- ============================================================================
-- JOB DESCRIPTIONS
-- ============================================================================

-- Recruiter + active status (if not exists)
CREATE INDEX IF NOT EXISTS idx_job_descriptions_recruiter_active 
ON job_descriptions(recruiter_id, is_active) 
WHERE is_active = true;

-- Hiring status filtering
CREATE INDEX IF NOT EXISTS idx_job_descriptions_recruiter_hiring_status 
ON job_descriptions(recruiter_id, hiring_status);

-- ============================================================================
-- SENT EMAILS (for email history queries)
-- ============================================================================

-- Recruiter + date range queries
CREATE INDEX IF NOT EXISTS idx_sent_emails_recruiter_created 
ON sent_emails(recruiter_id, created_at DESC);

-- Job description lookups
CREATE INDEX IF NOT EXISTS idx_sent_emails_job 
ON sent_emails(job_description_id) 
WHERE job_description_id IS NOT NULL;

-- Candidate lookups
CREATE INDEX IF NOT EXISTS idx_sent_emails_candidate 
ON sent_emails(candidate_id) 
WHERE candidate_id IS NOT NULL;

