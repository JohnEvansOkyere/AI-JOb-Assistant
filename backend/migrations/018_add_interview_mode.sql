-- Migration: Add Interview Mode Support
-- Adds interview_mode column to support text and voice interview modes
-- Created: 2025-12-27

-- ============================================================================
-- INTERVIEW TICKETS: Add interview_mode column
-- ============================================================================

-- Add interview_mode to interview_tickets table
-- 'text' = text-based interview (typing answers)
-- 'voice' = voice-based interview (speaking answers)
-- Default to 'text' for backward compatibility
ALTER TABLE interview_tickets 
ADD COLUMN IF NOT EXISTS interview_mode TEXT NOT NULL DEFAULT 'text'
CHECK (interview_mode IN ('text', 'voice'));

-- Create index for filtering by mode
CREATE INDEX IF NOT EXISTS idx_interview_tickets_mode 
ON interview_tickets(interview_mode);

-- Add comment
COMMENT ON COLUMN interview_tickets.interview_mode IS 'Interview mode: "text" for text-based (typing) or "voice" for voice-based (speaking). Set by recruiter when creating ticket.';

-- ============================================================================
-- INTERVIEWS: Add interview_mode column (inherited from ticket)
-- ============================================================================

-- Add interview_mode to interviews table for easier querying
-- This will be populated from the ticket when interview is created
ALTER TABLE interviews 
ADD COLUMN IF NOT EXISTS interview_mode TEXT
CHECK (interview_mode IN ('text', 'voice'));

-- Create index for filtering by mode
CREATE INDEX IF NOT EXISTS idx_interviews_mode 
ON interviews(interview_mode);

-- Add comment
COMMENT ON COLUMN interviews.interview_mode IS 'Interview mode inherited from ticket: "text" for text-based or "voice" for voice-based interviews.';

-- ============================================================================
-- UPDATE EXISTING RECORDS (if any)
-- ============================================================================

-- Set all existing interview_tickets to 'text' mode (backward compatible)
UPDATE interview_tickets 
SET interview_mode = 'text' 
WHERE interview_mode IS NULL;

-- Set all existing interviews to 'text' mode (backward compatible)
UPDATE interviews 
SET interview_mode = 'text' 
WHERE interview_mode IS NULL;

