-- Migration 003: Add Custom Application Forms
-- Allows recruiters to create custom application forms with additional fields
-- Run this migration after the initial schema and application tables are created

-- ============================================================================
-- APPLICATION FORM FIELDS TABLE
-- Stores custom form fields for each job description
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.application_form_fields (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_description_id UUID NOT NULL REFERENCES public.job_descriptions(id) ON DELETE CASCADE,
    field_key TEXT NOT NULL, -- Unique key for the field (e.g., "years_experience", "salary_expectation")
    field_label TEXT NOT NULL, -- Display label (e.g., "Years of Experience")
    field_type TEXT NOT NULL, -- text, email, tel, number, textarea, select, checkbox, radio, date
    field_options JSONB, -- For select, radio, checkbox options: {"options": ["Option 1", "Option 2"]}
    is_required BOOLEAN DEFAULT FALSE,
    placeholder TEXT,
    help_text TEXT, -- Helper text shown below the field
    validation_rules JSONB, -- e.g., {"min": 0, "max": 100, "pattern": "^[0-9]+$"}
    order_index INTEGER NOT NULL DEFAULT 0, -- Order in which fields appear
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(job_description_id, field_key)
);

-- ============================================================================
-- APPLICATION FORM RESPONSES TABLE
-- Stores responses to custom form fields
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.application_form_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    application_id UUID NOT NULL REFERENCES public.job_applications(id) ON DELETE CASCADE,
    field_key TEXT NOT NULL, -- References application_form_fields.field_key
    field_value TEXT, -- Stored as text (JSON for complex types)
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(application_id, field_key)
);

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_form_fields_job ON public.application_form_fields(job_description_id);
CREATE INDEX IF NOT EXISTS idx_form_fields_order ON public.application_form_fields(job_description_id, order_index);
CREATE INDEX IF NOT EXISTS idx_form_responses_application ON public.application_form_responses(application_id);
CREATE INDEX IF NOT EXISTS idx_form_responses_field ON public.application_form_responses(field_key);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

ALTER TABLE public.application_form_fields ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.application_form_responses ENABLE ROW LEVEL SECURITY;

-- Form Fields: Recruiters can manage fields for their jobs
CREATE POLICY "Recruiters can manage form fields for their jobs" ON public.application_form_fields
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.job_descriptions jd
            WHERE jd.id = application_form_fields.job_description_id
            AND jd.recruiter_id = auth.uid()
        )
    );

-- Form Fields: Public can view fields for active jobs (to fill the form)
CREATE POLICY "Public can view form fields for active jobs" ON public.application_form_fields
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.job_descriptions jd
            WHERE jd.id = application_form_fields.job_description_id
            AND jd.is_active = TRUE
        )
    );

-- Form Responses: Recruiters can view responses for their job applications
CREATE POLICY "Recruiters can view form responses for their applications" ON public.application_form_responses
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.job_applications ja
            JOIN public.job_descriptions jd ON jd.id = ja.job_description_id
            WHERE ja.id = application_form_responses.application_id
            AND jd.recruiter_id = auth.uid()
        )
    );

-- Form Responses: Public can create responses (when submitting application)
CREATE POLICY "Public can create form responses" ON public.application_form_responses
    FOR INSERT WITH CHECK (true);

-- ============================================================================
-- TRIGGERS
-- ============================================================================

CREATE TRIGGER update_form_fields_updated_at BEFORE UPDATE ON public.application_form_fields
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

