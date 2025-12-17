-- Migration: Email System with Branding and Calendar Integration
-- Creates tables for email templates, company branding, sent emails, and calendar events

-- Company Branding/Letterhead
CREATE TABLE IF NOT EXISTS company_branding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Company Information
    company_name VARCHAR(255) NOT NULL,
    company_logo_url TEXT,
    company_website TEXT,
    company_address TEXT,
    company_phone VARCHAR(50),
    company_email VARCHAR(255),
    
    -- Branding Colors
    primary_color VARCHAR(7) DEFAULT '#2563eb',  -- Hex color
    secondary_color VARCHAR(7) DEFAULT '#1e40af',
    accent_color VARCHAR(7) DEFAULT '#3b82f6',
    
    -- Email Signature
    email_signature TEXT,  -- HTML signature
    sender_name VARCHAR(255),
    sender_title VARCHAR(255),
    
    -- Letterhead Settings
    letterhead_header_html TEXT,  -- Custom HTML header
    letterhead_footer_html TEXT,  -- Custom HTML footer
    letterhead_background_color VARCHAR(7) DEFAULT '#ffffff',
    
    -- Metadata
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_recruiter_default UNIQUE (recruiter_id, is_default) DEFERRABLE INITIALLY DEFERRED
);

-- Email Templates
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    branding_id UUID REFERENCES company_branding(id) ON DELETE SET NULL,
    
    -- Template Info
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    body_html TEXT NOT NULL,  -- HTML email body
    body_text TEXT,  -- Plain text fallback
    
    -- Template Type
    template_type VARCHAR(50) NOT NULL DEFAULT 'custom',  -- custom, interview_ticket, application_received, rejection, offer
    is_system_template BOOLEAN DEFAULT false,  -- System templates can't be deleted
    
    -- Variables/Placeholders
    available_variables JSONB DEFAULT '[]',  -- e.g., ["{{candidate_name}}", "{{ticket_code}}", "{{job_title}}"]
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sent Emails (Email History)
CREATE TABLE IF NOT EXISTS sent_emails (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id UUID REFERENCES email_templates(id) ON DELETE SET NULL,
    branding_id UUID REFERENCES company_branding(id) ON DELETE SET NULL,
    
    -- Recipient
    recipient_email VARCHAR(255) NOT NULL,
    recipient_name VARCHAR(255),
    candidate_id UUID REFERENCES candidates(id) ON DELETE SET NULL,
    
    -- Email Content
    subject VARCHAR(500) NOT NULL,
    body_html TEXT NOT NULL,
    body_text TEXT,
    
    -- Email Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, sent, delivered, failed, bounced
    external_email_id VARCHAR(255),  -- ID from email service (Resend, etc.)
    error_message TEXT,
    
    -- Related Entities
    job_description_id UUID REFERENCES job_descriptions(id) ON DELETE SET NULL,
    interview_ticket_id UUID REFERENCES interview_tickets(id) ON DELETE SET NULL,
    application_id UUID REFERENCES job_applications(id) ON DELETE SET NULL,
    
    -- Metadata
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Calendar Events (Interview Bookings)
CREATE TABLE IF NOT EXISTS calendar_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    candidate_id UUID NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    job_description_id UUID REFERENCES job_descriptions(id) ON DELETE SET NULL,
    interview_id UUID REFERENCES interviews(id) ON DELETE SET NULL,
    
    -- Event Details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    location VARCHAR(500),  -- Physical location or video link
    is_virtual BOOLEAN DEFAULT false,
    video_link TEXT,  -- Zoom, Google Meet, etc.
    
    -- Timing
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Calendar Integration
    external_calendar_id VARCHAR(255),  -- Google Calendar event ID, etc.
    external_calendar_provider VARCHAR(50),  -- google, outlook, caldav
    calendar_sync_status VARCHAR(50) DEFAULT 'pending',  -- pending, synced, failed
    
    -- Attendees
    attendee_emails TEXT[] DEFAULT ARRAY[]::TEXT[],
    attendee_names TEXT[] DEFAULT ARRAY[]::TEXT[],
    
    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled',  -- scheduled, confirmed, cancelled, completed
    reminder_sent BOOLEAN DEFAULT false,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_time_range CHECK (end_time > start_time)
);

-- Calendar Integration Credentials (OAuth tokens, etc.)
CREATE TABLE IF NOT EXISTS calendar_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recruiter_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Provider Info
    provider VARCHAR(50) NOT NULL,  -- google, outlook, caldav
    provider_account_email VARCHAR(255) NOT NULL,
    
    -- OAuth Tokens (encrypted in production)
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Sync Settings
    is_active BOOLEAN DEFAULT true,
    auto_sync BOOLEAN DEFAULT true,
    sync_direction VARCHAR(20) DEFAULT 'bidirectional',  -- one_way_out, one_way_in, bidirectional
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_provider_account UNIQUE (recruiter_id, provider, provider_account_email)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_company_branding_recruiter ON company_branding(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_company_branding_default ON company_branding(recruiter_id, is_default) WHERE is_default = true;

CREATE INDEX IF NOT EXISTS idx_email_templates_recruiter ON email_templates(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_email_templates_type ON email_templates(template_type);

CREATE INDEX IF NOT EXISTS idx_sent_emails_recruiter ON sent_emails(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_sent_emails_candidate ON sent_emails(candidate_id);
CREATE INDEX IF NOT EXISTS idx_sent_emails_status ON sent_emails(status);
CREATE INDEX IF NOT EXISTS idx_sent_emails_created ON sent_emails(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_calendar_events_recruiter ON calendar_events(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_candidate ON calendar_events(candidate_id);
CREATE INDEX IF NOT EXISTS idx_calendar_events_start_time ON calendar_events(start_time);
CREATE INDEX IF NOT EXISTS idx_calendar_events_status ON calendar_events(status);

CREATE INDEX IF NOT EXISTS idx_calendar_integrations_recruiter ON calendar_integrations(recruiter_id);
CREATE INDEX IF NOT EXISTS idx_calendar_integrations_provider ON calendar_integrations(provider, is_active);

-- RLS Policies
ALTER TABLE company_branding ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE sent_emails ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_integrations ENABLE ROW LEVEL SECURITY;

-- Company Branding Policies
CREATE POLICY "Recruiters can view their own branding"
    ON company_branding FOR SELECT
    USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can insert their own branding"
    ON company_branding FOR INSERT
    WITH CHECK (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can update their own branding"
    ON company_branding FOR UPDATE
    USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can delete their own branding"
    ON company_branding FOR DELETE
    USING (auth.uid() = recruiter_id);

-- Email Templates Policies
CREATE POLICY "Recruiters can view their own templates"
    ON email_templates FOR SELECT
    USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can insert their own templates"
    ON email_templates FOR INSERT
    WITH CHECK (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can update their own templates"
    ON email_templates FOR UPDATE
    USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can delete their own templates"
    ON email_templates FOR DELETE
    USING (auth.uid() = recruiter_id AND is_system_template = false);

-- Sent Emails Policies
CREATE POLICY "Recruiters can view their own sent emails"
    ON sent_emails FOR SELECT
    USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can insert their own sent emails"
    ON sent_emails FOR INSERT
    WITH CHECK (auth.uid() = recruiter_id);

-- Calendar Events Policies
CREATE POLICY "Recruiters can view their own calendar events"
    ON calendar_events FOR SELECT
    USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can insert their own calendar events"
    ON calendar_events FOR INSERT
    WITH CHECK (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can update their own calendar events"
    ON calendar_events FOR UPDATE
    USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can delete their own calendar events"
    ON calendar_events FOR DELETE
    USING (auth.uid() = recruiter_id);

-- Calendar Integrations Policies
CREATE POLICY "Recruiters can view their own calendar integrations"
    ON calendar_integrations FOR SELECT
    USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can insert their own calendar integrations"
    ON calendar_integrations FOR INSERT
    WITH CHECK (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can update their own calendar integrations"
    ON calendar_integrations FOR UPDATE
    USING (auth.uid() = recruiter_id);

CREATE POLICY "Recruiters can delete their own calendar integrations"
    ON calendar_integrations FOR DELETE
    USING (auth.uid() = recruiter_id);

-- Updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_company_branding_updated_at
    BEFORE UPDATE ON company_branding
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_templates_updated_at
    BEFORE UPDATE ON email_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sent_emails_updated_at
    BEFORE UPDATE ON sent_emails
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calendar_events_updated_at
    BEFORE UPDATE ON calendar_events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_calendar_integrations_updated_at
    BEFORE UPDATE ON calendar_integrations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

