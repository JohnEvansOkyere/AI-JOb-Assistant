    -- Migration: Admin support and AI usage logging
    -- Adds admin role support and comprehensive AI usage tracking

    -- Add is_admin field to users table
    ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE NOT NULL;

    -- Create index for admin lookup
    CREATE INDEX IF NOT EXISTS idx_users_is_admin ON public.users(is_admin) WHERE is_admin = TRUE;

    -- Create AI usage logs table
    CREATE TABLE IF NOT EXISTS public.ai_usage_logs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        
        -- Organization/User context
        user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
        recruiter_id UUID REFERENCES public.users(id) ON DELETE SET NULL, -- Same as user_id but more explicit
        
        -- Resource context (what was this AI call for?)
        interview_id UUID REFERENCES public.interviews(id) ON DELETE SET NULL,
        job_description_id UUID REFERENCES public.job_descriptions(id) ON DELETE SET NULL,
        candidate_id UUID REFERENCES public.candidates(id) ON DELETE SET NULL,
        
        -- AI provider details
        provider_name VARCHAR(50) NOT NULL, -- 'openai', 'groq', 'gemini', 'elevenlabs', 'whisper', 'deepgram'
        model_name VARCHAR(100), -- e.g., 'gpt-4o-mini', 'eleven_multilingual_v2'
        feature_name VARCHAR(100) NOT NULL, -- 'question_generation', 'response_analysis', 'tts_synthesis', 'stt_transcription', 'cv_screening', 'interview_analysis'
        
        -- Usage metrics
        prompt_tokens INTEGER, -- For OpenAI/Groq/Gemini
        completion_tokens INTEGER, -- For OpenAI/Groq/Gemini
        total_tokens INTEGER, -- For OpenAI/Groq/Gemini
        characters_used INTEGER, -- For ElevenLabs TTS (text length)
        audio_duration_seconds DECIMAL(10, 2), -- For STT/TTS audio length
        
        -- Cost calculation
        estimated_cost_usd DECIMAL(10, 6) DEFAULT 0, -- Cost in USD
        cost_model_version VARCHAR(20) DEFAULT '1.0', -- Track cost calculation version
        
        -- Performance metrics
        latency_ms INTEGER, -- Request latency in milliseconds
        status VARCHAR(20) NOT NULL DEFAULT 'success', -- 'success', 'failure', 'error'
        error_message TEXT, -- Error details if status is failure/error
        
        -- Metadata
        prompt_version VARCHAR(50), -- Track prompt versions for analysis
        metadata JSONB, -- Additional context (request details, etc.)
        
        -- Timestamps
        created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
    );

    -- Create indexes for efficient queries
    CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_user_id ON public.ai_usage_logs(user_id);
    CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_recruiter_id ON public.ai_usage_logs(recruiter_id);
    CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_interview_id ON public.ai_usage_logs(interview_id);
    CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_job_description_id ON public.ai_usage_logs(job_description_id);
    CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_provider_name ON public.ai_usage_logs(provider_name);
    CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_feature_name ON public.ai_usage_logs(feature_name);
    CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_status ON public.ai_usage_logs(status);
    CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_created_at ON public.ai_usage_logs(created_at);
    CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_created_at_date ON public.ai_usage_logs(DATE(created_at));

    -- Composite indexes for common queries
    CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_recruiter_created ON public.ai_usage_logs(recruiter_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_provider_feature ON public.ai_usage_logs(provider_name, feature_name);
    CREATE INDEX IF NOT EXISTS idx_ai_usage_logs_status_created ON public.ai_usage_logs(status, created_at DESC);

    -- Enable RLS
    ALTER TABLE public.ai_usage_logs ENABLE ROW LEVEL SECURITY;

    -- RLS Policies: Admins can view all, users can view their own
    CREATE POLICY "Admins can view all AI usage logs" ON public.ai_usage_logs
        FOR SELECT USING (
            EXISTS (
                SELECT 1 FROM public.users
                WHERE users.id = (SELECT auth.uid())
                AND users.is_admin = TRUE
            )
        );

    CREATE POLICY "Users can view their own AI usage logs" ON public.ai_usage_logs
        FOR SELECT USING (
            recruiter_id = (SELECT auth.uid())
        );

    -- System can insert logs (using service role)
    -- Note: Service role bypasses RLS, so inserts from backend will work
    -- This policy allows authenticated users to insert their own logs (if needed)
    CREATE POLICY "Users can insert their own AI usage logs" ON public.ai_usage_logs
        FOR INSERT WITH CHECK (
            recruiter_id = (SELECT auth.uid())
        );

    -- Comments for documentation
    COMMENT ON TABLE public.ai_usage_logs IS 'Comprehensive logging of all AI service usage for cost tracking and monitoring';
    COMMENT ON COLUMN public.ai_usage_logs.provider_name IS 'AI provider: openai, groq, gemini, elevenlabs, whisper, deepgram';
    COMMENT ON COLUMN public.ai_usage_logs.feature_name IS 'Feature using AI: question_generation, response_analysis, tts_synthesis, stt_transcription, cv_screening, interview_analysis';
    COMMENT ON COLUMN public.ai_usage_logs.estimated_cost_usd IS 'Estimated cost in USD based on provider pricing';
    COMMENT ON COLUMN public.ai_usage_logs.cost_model_version IS 'Version of cost calculation model for tracking pricing changes';

