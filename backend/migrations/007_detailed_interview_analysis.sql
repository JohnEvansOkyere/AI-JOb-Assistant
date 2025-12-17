-- Migration: Comprehensive Detailed Interview Analysis Table
-- Deep analysis of AI interview performance with soft skills, technical skills, and sentiment
-- Created: 2025-12-17

-- Create the detailed_interview_analysis table
CREATE TABLE IF NOT EXISTS detailed_interview_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    interview_id UUID NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    
    -- Overall Scores (0-100)
    overall_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    technical_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    soft_skills_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    communication_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    
    -- Detailed Soft Skills Scores (0-100 each)
    leadership_score DECIMAL(5,2) DEFAULT 0,
    teamwork_score DECIMAL(5,2) DEFAULT 0,
    problem_solving_score DECIMAL(5,2) DEFAULT 0,
    adaptability_score DECIMAL(5,2) DEFAULT 0,
    creativity_score DECIMAL(5,2) DEFAULT 0,
    emotional_intelligence_score DECIMAL(5,2) DEFAULT 0,
    time_management_score DECIMAL(5,2) DEFAULT 0,
    conflict_resolution_score DECIMAL(5,2) DEFAULT 0,
    
    -- Communication Assessment (0-100 each)
    clarity_score DECIMAL(5,2) DEFAULT 0,
    articulation_score DECIMAL(5,2) DEFAULT 0,
    confidence_score DECIMAL(5,2) DEFAULT 0,
    listening_score DECIMAL(5,2) DEFAULT 0,
    persuasion_score DECIMAL(5,2) DEFAULT 0,
    
    -- Technical Assessment
    technical_depth_score DECIMAL(5,2) DEFAULT 0,
    technical_breadth_score DECIMAL(5,2) DEFAULT 0,
    practical_application_score DECIMAL(5,2) DEFAULT 0,
    industry_knowledge_score DECIMAL(5,2) DEFAULT 0,
    
    -- Sentiment Analysis
    overall_sentiment VARCHAR(20) DEFAULT 'neutral', -- positive, neutral, negative, mixed
    sentiment_score DECIMAL(5,2) DEFAULT 50, -- 0-100 (0=very negative, 100=very positive)
    enthusiasm_level VARCHAR(20) DEFAULT 'moderate', -- high, moderate, low
    stress_indicators TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Behavioral Indicators
    honesty_indicators TEXT[] DEFAULT ARRAY[]::TEXT[],
    red_flag_behaviors TEXT[] DEFAULT ARRAY[]::TEXT[],
    positive_behaviors TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Detailed Analysis (JSONB for flexibility)
    soft_skills_analysis JSONB DEFAULT '{}',
    technical_analysis JSONB DEFAULT '{}',
    communication_analysis JSONB DEFAULT '{}',
    sentiment_analysis JSONB DEFAULT '{}',
    behavioral_analysis JSONB DEFAULT '{}',
    
    -- Question-by-Question Breakdown
    question_analyses JSONB DEFAULT '[]', -- Array of per-question analyses
    
    -- Summary Arrays
    key_strengths TEXT[] DEFAULT ARRAY[]::TEXT[],
    areas_for_improvement TEXT[] DEFAULT ARRAY[]::TEXT[],
    notable_quotes TEXT[] DEFAULT ARRAY[]::TEXT[],
    follow_up_topics TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Culture Fit Assessment
    culture_fit_score DECIMAL(5,2) DEFAULT 0,
    culture_fit_notes TEXT DEFAULT '',
    
    -- Role Fit Assessment
    role_fit_score DECIMAL(5,2) DEFAULT 0,
    role_fit_analysis TEXT DEFAULT '',
    
    -- Final Recommendation
    recommendation VARCHAR(50) NOT NULL DEFAULT 'under_review',
    recommendation_confidence DECIMAL(5,2) DEFAULT 0, -- 0-100
    recommendation_summary TEXT DEFAULT '',
    detailed_recommendation TEXT DEFAULT '',
    
    -- Interview Metadata
    total_questions INTEGER DEFAULT 0,
    total_responses INTEGER DEFAULT 0,
    average_response_length INTEGER DEFAULT 0,
    interview_duration_seconds INTEGER DEFAULT 0,
    
    -- Metadata
    analysis_version VARCHAR(20) DEFAULT '1.0',
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_overall_score CHECK (overall_score >= 0 AND overall_score <= 100),
    CONSTRAINT valid_technical_score CHECK (technical_score >= 0 AND technical_score <= 100),
    CONSTRAINT valid_soft_skills_score CHECK (soft_skills_score >= 0 AND soft_skills_score <= 100),
    CONSTRAINT valid_communication_score CHECK (communication_score >= 0 AND communication_score <= 100),
    CONSTRAINT valid_sentiment CHECK (overall_sentiment IN ('positive', 'neutral', 'negative', 'mixed')),
    CONSTRAINT valid_enthusiasm CHECK (enthusiasm_level IN ('high', 'moderate', 'low')),
    CONSTRAINT valid_recommendation CHECK (recommendation IN ('strong_hire', 'hire', 'maybe', 'no_hire', 'under_review'))
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_detailed_interview_analysis_interview_id ON detailed_interview_analysis(interview_id);
CREATE INDEX IF NOT EXISTS idx_detailed_interview_analysis_overall_score ON detailed_interview_analysis(overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_detailed_interview_analysis_recommendation ON detailed_interview_analysis(recommendation);
CREATE INDEX IF NOT EXISTS idx_detailed_interview_analysis_analyzed_at ON detailed_interview_analysis(analyzed_at DESC);

-- Add unique constraint to ensure one analysis per interview
CREATE UNIQUE INDEX IF NOT EXISTS idx_detailed_interview_analysis_unique_interview ON detailed_interview_analysis(interview_id);

-- Enable RLS
ALTER TABLE detailed_interview_analysis ENABLE ROW LEVEL SECURITY;

-- RLS Policies (recruiters can view their own interviews' analyses)
CREATE POLICY "Recruiters can view their interview analyses"
ON detailed_interview_analysis
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM interviews i
        JOIN job_descriptions jd ON i.job_description_id = jd.id
        WHERE i.id = detailed_interview_analysis.interview_id
        AND jd.recruiter_id = auth.uid()
    )
);

-- Service role can do everything
CREATE POLICY "Service role full access on detailed_interview_analysis"
ON detailed_interview_analysis
FOR ALL
USING (auth.role() = 'service_role')
WITH CHECK (auth.role() = 'service_role');

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_detailed_interview_analysis_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_detailed_interview_analysis_updated_at
    BEFORE UPDATE ON detailed_interview_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_detailed_interview_analysis_updated_at();

-- Comments for documentation
COMMENT ON TABLE detailed_interview_analysis IS 'Comprehensive AI-powered analysis of interview performance';
COMMENT ON COLUMN detailed_interview_analysis.overall_score IS 'Weighted aggregate score of all assessment areas (0-100)';
COMMENT ON COLUMN detailed_interview_analysis.sentiment_score IS 'Overall sentiment from 0 (very negative) to 100 (very positive)';
COMMENT ON COLUMN detailed_interview_analysis.question_analyses IS 'JSON array containing detailed analysis for each Q&A pair';

