-- Migration: Comprehensive CV Detailed Screening Table
-- Similar to Resume Worded's detailed analysis system
-- Created: 2025-12-17

-- Create the cv_detailed_screening table
CREATE TABLE IF NOT EXISTS cv_detailed_screening (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID NOT NULL REFERENCES job_applications(id) ON DELETE CASCADE,
    cv_id UUID NOT NULL REFERENCES cvs(id) ON DELETE CASCADE,
    
    -- Overall score (0-100)
    overall_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    
    -- Section scores (0-100 each)
    format_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    structure_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    experience_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    education_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    skills_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    language_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    ats_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    impact_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    
    -- Job match score (specific to job description)
    job_match_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    
    -- Detailed analysis (stored as JSONB for flexibility)
    format_analysis JSONB DEFAULT '{}',
    structure_analysis JSONB DEFAULT '{}',
    experience_analysis JSONB DEFAULT '{}',
    education_analysis JSONB DEFAULT '{}',
    skills_analysis JSONB DEFAULT '{}',
    language_analysis JSONB DEFAULT '{}',
    ats_analysis JSONB DEFAULT '{}',
    impact_analysis JSONB DEFAULT '{}',
    
    -- Summary arrays
    top_strengths TEXT[] DEFAULT ARRAY[]::TEXT[],
    critical_issues TEXT[] DEFAULT ARRAY[]::TEXT[],
    improvement_suggestions TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Hiring recommendation
    recommendation VARCHAR(50) NOT NULL DEFAULT 'maybe_qualified',
    recommendation_reason TEXT DEFAULT '',
    
    -- Metadata
    analysis_version VARCHAR(20) DEFAULT '1.0',
    screened_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_overall_score CHECK (overall_score >= 0 AND overall_score <= 100),
    CONSTRAINT valid_format_score CHECK (format_score >= 0 AND format_score <= 100),
    CONSTRAINT valid_structure_score CHECK (structure_score >= 0 AND structure_score <= 100),
    CONSTRAINT valid_experience_score CHECK (experience_score >= 0 AND experience_score <= 100),
    CONSTRAINT valid_education_score CHECK (education_score >= 0 AND education_score <= 100),
    CONSTRAINT valid_skills_score CHECK (skills_score >= 0 AND skills_score <= 100),
    CONSTRAINT valid_language_score CHECK (language_score >= 0 AND language_score <= 100),
    CONSTRAINT valid_ats_score CHECK (ats_score >= 0 AND ats_score <= 100),
    CONSTRAINT valid_impact_score CHECK (impact_score >= 0 AND impact_score <= 100),
    CONSTRAINT valid_job_match_score CHECK (job_match_score >= 0 AND job_match_score <= 100),
    CONSTRAINT valid_recommendation CHECK (recommendation IN ('qualified', 'maybe_qualified', 'not_qualified'))
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_cv_detailed_screening_application_id ON cv_detailed_screening(application_id);
CREATE INDEX IF NOT EXISTS idx_cv_detailed_screening_cv_id ON cv_detailed_screening(cv_id);
CREATE INDEX IF NOT EXISTS idx_cv_detailed_screening_overall_score ON cv_detailed_screening(overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_cv_detailed_screening_recommendation ON cv_detailed_screening(recommendation);
CREATE INDEX IF NOT EXISTS idx_cv_detailed_screening_screened_at ON cv_detailed_screening(screened_at DESC);

-- Unique constraint: one detailed screening per application
CREATE UNIQUE INDEX IF NOT EXISTS idx_cv_detailed_screening_unique_app ON cv_detailed_screening(application_id);

-- Enable Row Level Security
ALTER TABLE cv_detailed_screening ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Recruiters can view all screening results for their jobs
CREATE POLICY "recruiters_view_detailed_screening" ON cv_detailed_screening
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM job_applications ja
            JOIN job_descriptions jd ON ja.job_description_id = jd.id
            WHERE ja.id = cv_detailed_screening.application_id
            AND jd.recruiter_id = auth.uid()
        )
    );

-- Service role can do everything (for backend operations)
CREATE POLICY "service_role_full_access_detailed_screening" ON cv_detailed_screening
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'service_role');

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_cv_detailed_screening_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto-updating updated_at
DROP TRIGGER IF EXISTS trigger_update_cv_detailed_screening_updated_at ON cv_detailed_screening;
CREATE TRIGGER trigger_update_cv_detailed_screening_updated_at
    BEFORE UPDATE ON cv_detailed_screening
    FOR EACH ROW
    EXECUTE FUNCTION update_cv_detailed_screening_updated_at();

-- Comment on table
COMMENT ON TABLE cv_detailed_screening IS 'Comprehensive CV analysis results similar to Resume Worded, with detailed scoring across multiple categories';

-- Comments on columns
COMMENT ON COLUMN cv_detailed_screening.overall_score IS 'Overall CV quality score (0-100)';
COMMENT ON COLUMN cv_detailed_screening.format_score IS 'Formatting quality: consistency, template, fonts, length';
COMMENT ON COLUMN cv_detailed_screening.structure_score IS 'Structure quality: section order, contact info, unnecessary sections';
COMMENT ON COLUMN cv_detailed_screening.experience_score IS 'Work experience quality: action verbs, quantification, accomplishments';
COMMENT ON COLUMN cv_detailed_screening.education_score IS 'Education section completeness and relevance';
COMMENT ON COLUMN cv_detailed_screening.skills_score IS 'Skills section: technical, soft skills, job match';
COMMENT ON COLUMN cv_detailed_screening.language_score IS 'Writing quality: grammar, spelling, tense, no pronouns';
COMMENT ON COLUMN cv_detailed_screening.ats_score IS 'ATS compatibility: parsability, keywords, format';
COMMENT ON COLUMN cv_detailed_screening.impact_score IS 'Overall impact: brevity, clarity, professionalism';
COMMENT ON COLUMN cv_detailed_screening.job_match_score IS 'Match score specific to the job description';

