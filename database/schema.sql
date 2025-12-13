-- ============================================================================
-- AI Voice Interview Platform - Database Schema
-- Supabase PostgreSQL Database
-- ============================================================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search

-- ============================================================================
-- USERS TABLE (Recruiters)
-- Extends Supabase auth.users with additional recruiter information
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    company_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- CANDIDATES TABLE
-- Stores candidate profile information
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.candidates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT NOT NULL,
    full_name TEXT,
    phone TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- JOB DESCRIPTIONS TABLE
-- Stores job postings created by recruiters
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.job_descriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recruiter_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL, -- Full job description text
    requirements TEXT, -- Structured requirements
    location TEXT,
    employment_type TEXT, -- full-time, part-time, contract, etc.
    experience_level TEXT, -- junior, mid, senior
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================================================
-- CVs TABLE
-- Stores CV files and parsed content
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.cvs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID NOT NULL REFERENCES public.candidates(id) ON DELETE CASCADE,
    job_description_id UUID REFERENCES public.job_descriptions(id) ON DELETE SET NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL, -- Supabase Storage path
    file_size BIGINT,
    mime_type TEXT,
    parsed_text TEXT, -- Extracted text from CV
    parsed_json JSONB, -- Structured CV data (skills, experience, etc.)
    uploaded_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- INTERVIEW TICKETS TABLE
-- One-time access tickets for candidates
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.interview_tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID NOT NULL REFERENCES public.candidates(id) ON DELETE CASCADE,
    job_description_id UUID NOT NULL REFERENCES public.job_descriptions(id) ON DELETE CASCADE,
    ticket_code TEXT UNIQUE NOT NULL, -- Unique ticket identifier
    is_used BOOLEAN DEFAULT FALSE,
    is_expired BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ, -- Optional expiration
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    created_by UUID REFERENCES public.users(id) ON DELETE SET NULL
);

-- ============================================================================
-- INTERVIEWS TABLE
-- Interview session records
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.interviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    candidate_id UUID NOT NULL REFERENCES public.candidates(id) ON DELETE CASCADE,
    job_description_id UUID NOT NULL REFERENCES public.job_descriptions(id) ON DELETE CASCADE,
    ticket_id UUID NOT NULL REFERENCES public.interview_tickets(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'pending', -- pending, in_progress, completed, cancelled
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    audio_file_path TEXT, -- Supabase Storage path to interview audio
    transcript TEXT, -- Full interview transcript
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- INTERVIEW QUESTIONS TABLE
-- Generated questions for each interview
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.interview_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interview_id UUID NOT NULL REFERENCES public.interviews(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type TEXT, -- warmup, skill, experience, soft_skill, wrapup
    skill_category TEXT, -- Which skill/requirement this targets
    order_index INTEGER NOT NULL,
    asked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- INTERVIEW RESPONSES TABLE
-- Candidate responses to questions
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.interview_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interview_id UUID NOT NULL REFERENCES public.interviews(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES public.interview_questions(id) ON DELETE CASCADE,
    response_text TEXT NOT NULL,
    response_audio_path TEXT, -- Optional audio clip
    timestamp_seconds INTEGER, -- Position in interview audio
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- INTERVIEW REPORTS TABLE
-- Final evaluation reports generated after interview
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.interview_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    interview_id UUID UNIQUE NOT NULL REFERENCES public.interviews(id) ON DELETE CASCADE,
    skill_match_score DECIMAL(5,2), -- Percentage match (0-100)
    experience_level TEXT, -- junior, mid, senior
    strengths TEXT[], -- Array of strength points
    weaknesses TEXT[], -- Array of weakness points
    red_flags TEXT[], -- Array of red flags
    hiring_recommendation TEXT, -- strong_hire, hire, neutral, no_hire
    recommendation_justification TEXT,
    full_report JSONB, -- Complete structured report
    recruiter_notes TEXT, -- Editable notes from recruiter
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ============================================================================
-- INDEXES
-- Performance optimization
-- ============================================================================

-- Users
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

-- Job Descriptions
CREATE INDEX IF NOT EXISTS idx_job_descriptions_recruiter ON public.job_descriptions(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_active ON public.job_descriptions(is_active) WHERE is_active = TRUE;

-- CVs
CREATE INDEX IF NOT EXISTS idx_cvs_candidate ON public.cvs(candidate_id);
CREATE INDEX IF NOT EXISTS idx_cvs_job_description ON public.cvs(job_description_id);
CREATE INDEX IF NOT EXISTS idx_cvs_parsed_text ON public.cvs USING gin(to_tsvector('english', parsed_text));

-- Interview Tickets
CREATE INDEX IF NOT EXISTS idx_tickets_code ON public.interview_tickets(ticket_code);
CREATE INDEX IF NOT EXISTS idx_tickets_candidate ON public.interview_tickets(candidate_id);
CREATE INDEX IF NOT EXISTS idx_tickets_job_description ON public.interview_tickets(job_description_id);
CREATE INDEX IF NOT EXISTS idx_tickets_used ON public.interview_tickets(is_used, is_expired);

-- Interviews
CREATE INDEX IF NOT EXISTS idx_interviews_candidate ON public.interviews(candidate_id);
CREATE INDEX IF NOT EXISTS idx_interviews_job_description ON public.interviews(job_description_id);
CREATE INDEX IF NOT EXISTS idx_interviews_ticket ON public.interviews(ticket_id);
CREATE INDEX IF NOT EXISTS idx_interviews_status ON public.interviews(status);

-- Interview Questions
CREATE INDEX IF NOT EXISTS idx_questions_interview ON public.interview_questions(interview_id);
CREATE INDEX IF NOT EXISTS idx_questions_order ON public.interview_questions(interview_id, order_index);

-- Interview Responses
CREATE INDEX IF NOT EXISTS idx_responses_interview ON public.interview_responses(interview_id);
CREATE INDEX IF NOT EXISTS idx_responses_question ON public.interview_responses(question_id);

-- Interview Reports
CREATE INDEX IF NOT EXISTS idx_reports_interview ON public.interview_reports(interview_id);
CREATE INDEX IF NOT EXISTS idx_reports_recommendation ON public.interview_reports(hiring_recommendation);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_descriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cvs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interview_reports ENABLE ROW LEVEL SECURITY;

-- Users: Recruiters can view/update their own profile
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Job Descriptions: Recruiters can manage their own job descriptions
CREATE POLICY "Recruiters can view own job descriptions" ON public.job_descriptions
    FOR SELECT USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can create own job descriptions" ON public.job_descriptions
    FOR INSERT WITH CHECK (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can update own job descriptions" ON public.job_descriptions
    FOR UPDATE USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can delete own job descriptions" ON public.job_descriptions
    FOR DELETE USING (auth.uid() = recruiter_id);

-- CVs: Recruiters can view CVs for their job descriptions
CREATE POLICY "Recruiters can view CVs for their jobs" ON public.cvs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.job_descriptions jd
            WHERE jd.id = cvs.job_description_id
            AND jd.recruiter_id = auth.uid()
        )
    );

-- Interview Tickets: Recruiters can manage tickets for their jobs
CREATE POLICY "Recruiters can view tickets for their jobs" ON public.interview_tickets
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.job_descriptions jd
            WHERE jd.id = interview_tickets.job_description_id
            AND jd.recruiter_id = auth.uid()
        )
    );

CREATE POLICY "Recruiters can create tickets for their jobs" ON public.interview_tickets
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.job_descriptions jd
            WHERE jd.id = interview_tickets.job_description_id
            AND jd.recruiter_id = auth.uid()
        )
    );

-- Interviews: Recruiters can view interviews for their jobs
CREATE POLICY "Recruiters can view interviews for their jobs" ON public.interviews
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.job_descriptions jd
            WHERE jd.id = interviews.job_description_id
            AND jd.recruiter_id = auth.uid()
        )
    );

-- Interview Questions: Recruiters can view questions for their interviews
CREATE POLICY "Recruiters can view questions for their interviews" ON public.interview_questions
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.interviews i
            JOIN public.job_descriptions jd ON jd.id = i.job_description_id
            WHERE i.id = interview_questions.interview_id
            AND jd.recruiter_id = auth.uid()
        )
    );

-- Interview Responses: Recruiters can view responses for their interviews
CREATE POLICY "Recruiters can view responses for their interviews" ON public.interview_responses
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.interviews i
            JOIN public.job_descriptions jd ON jd.id = i.job_description_id
            WHERE i.id = interview_responses.interview_id
            AND jd.recruiter_id = auth.uid()
        )
    );

-- Interview Reports: Recruiters can view and update reports for their interviews
CREATE POLICY "Recruiters can view reports for their interviews" ON public.interview_reports
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.interviews i
            JOIN public.job_descriptions jd ON jd.id = i.job_description_id
            WHERE i.id = interview_reports.interview_id
            AND jd.recruiter_id = auth.uid()
        )
    );

CREATE POLICY "Recruiters can update reports for their interviews" ON public.interview_reports
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.interviews i
            JOIN public.job_descriptions jd ON jd.id = i.job_description_id
            WHERE i.id = interview_reports.interview_id
            AND jd.recruiter_id = auth.uid()
        )
    );

-- Candidates: Public read for ticket validation (limited)
-- Note: Full candidate access should be through authenticated endpoints

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_descriptions_updated_at BEFORE UPDATE ON public.job_descriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_interview_reports_updated_at BEFORE UPDATE ON public.interview_reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Generate unique ticket code
CREATE OR REPLACE FUNCTION generate_ticket_code()
RETURNS TEXT AS $$
DECLARE
    chars TEXT := 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; -- Exclude ambiguous chars
    result TEXT := '';
    i INTEGER;
BEGIN
    FOR i IN 1..12 LOOP
        result := result || substr(chars, floor(random() * length(chars) + 1)::int, 1);
    END LOOP;
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STORAGE BUCKETS (Supabase Storage)
-- ============================================================================

-- Note: These need to be created via Supabase Dashboard or API
-- Bucket names:
-- - 'cvs' - For CV file uploads
-- - 'interview-audio' - For interview audio recordings
-- - 'response-audio' - For individual response audio clips (optional)

-- Storage policies should be configured to:
-- - Allow recruiters to upload CVs
-- - Allow system to store interview audio
-- - Allow recruiters to read all files in their job's context

