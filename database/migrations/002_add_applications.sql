-- Migration 002: Add Job Applications and Screening
-- Adds tables for job applications and CV screening results

-- ============================================================================
-- JOB APPLICATIONS TABLE
-- Stores job applications from candidates
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.job_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_description_id UUID NOT NULL REFERENCES public.job_descriptions(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES public.candidates(id) ON DELETE CASCADE,
    cv_id UUID REFERENCES public.cvs(id) ON DELETE SET NULL,
    cover_letter TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, screening, qualified, rejected, interview_scheduled
    applied_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    screened_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(job_description_id, candidate_id) -- One application per candidate per job
);

-- ============================================================================
-- CV SCREENING RESULTS TABLE
-- Stores AI screening results for applications
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.cv_screening_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID UNIQUE NOT NULL REFERENCES public.job_applications(id) ON DELETE CASCADE,
    match_score DECIMAL(5,2) NOT NULL, -- 0-100 percentage match
    skill_match_score DECIMAL(5,2), -- Skill-specific match
    experience_match_score DECIMAL(5,2), -- Experience match
    qualification_match_score DECIMAL(5,2), -- Qualification match
    strengths TEXT[], -- Array of matched strengths
    gaps TEXT[], -- Array of skill/experience gaps
    recommendation TEXT, -- qualified, maybe_qualified, not_qualified
    screening_notes TEXT, -- AI-generated notes
    screening_details JSONB, -- Full screening analysis
    screened_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_applications_job ON public.job_applications(job_description_id);
CREATE INDEX IF NOT EXISTS idx_applications_candidate ON public.job_applications(candidate_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON public.job_applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_cv ON public.job_applications(cv_id);
CREATE INDEX IF NOT EXISTS idx_screening_application ON public.cv_screening_results(application_id);
CREATE INDEX IF NOT EXISTS idx_screening_score ON public.cv_screening_results(match_score DESC);
CREATE INDEX IF NOT EXISTS idx_screening_recommendation ON public.cv_screening_results(recommendation);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

ALTER TABLE public.job_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cv_screening_results ENABLE ROW LEVEL SECURITY;

-- Job Applications: Recruiters can view applications for their jobs
CREATE POLICY "Recruiters can view applications for their jobs" ON public.job_applications
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.job_descriptions jd
            WHERE jd.id = job_applications.job_description_id
            AND jd.recruiter_id = auth.uid()
        )
    );

-- Job Applications: Public can create applications (no auth required for application)
-- Note: In production, you might want to add rate limiting or CAPTCHA
CREATE POLICY "Public can create applications" ON public.job_applications
    FOR INSERT WITH CHECK (true);

-- CV Screening Results: Recruiters can view screening for their job applications
CREATE POLICY "Recruiters can view screening for their applications" ON public.cv_screening_results
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.job_applications ja
            JOIN public.job_descriptions jd ON jd.id = ja.job_description_id
            WHERE ja.id = cv_screening_results.application_id
            AND jd.recruiter_id = auth.uid()
        )
    );

-- ============================================================================
-- TRIGGERS
-- ============================================================================

CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON public.job_applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

