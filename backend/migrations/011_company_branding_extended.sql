-- Migration: Extend company_branding with richer company settings
-- Adds optional fields for company profile, hiring preferences, and social links

ALTER TABLE company_branding
ADD COLUMN IF NOT EXISTS company_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS industry VARCHAR(150),
ADD COLUMN IF NOT EXISTS company_size VARCHAR(100),
ADD COLUMN IF NOT EXISTS headquarters_location TEXT,
ADD COLUMN IF NOT EXISTS company_description TEXT,
ADD COLUMN IF NOT EXISTS mission_statement TEXT,
ADD COLUMN IF NOT EXISTS values_statement TEXT,
ADD COLUMN IF NOT EXISTS linkedin_url TEXT,
ADD COLUMN IF NOT EXISTS twitter_url TEXT,
ADD COLUMN IF NOT EXISTS facebook_url TEXT,
ADD COLUMN IF NOT EXISTS instagram_url TEXT,
ADD COLUMN IF NOT EXISTS careers_page_url TEXT,
ADD COLUMN IF NOT EXISTS hiring_email VARCHAR(255),
ADD COLUMN IF NOT EXISTS default_timezone VARCHAR(100),
ADD COLUMN IF NOT EXISTS working_model VARCHAR(50); -- onsite, remote, hybrid


