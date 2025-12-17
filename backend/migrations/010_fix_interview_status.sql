-- Migration: Fix Interview Status
-- Updates interviews that have completed_at set but status is not 'completed'

-- Fix interviews that have completed_at but wrong status
UPDATE interviews 
SET status = 'completed'
WHERE completed_at IS NOT NULL 
  AND status != 'completed'
  AND status IN ('in_progress', 'pending');

-- Add a check constraint to ensure data integrity
-- If completed_at is set, status should be 'completed'
-- Note: This is a soft constraint - we'll handle it in application logic
-- as we might want to allow status changes after completion

-- Create a function to auto-update status when completed_at is set
CREATE OR REPLACE FUNCTION update_interview_status_on_completion()
RETURNS TRIGGER AS $$
BEGIN
    -- If completed_at is set and status is not completed, update it
    IF NEW.completed_at IS NOT NULL AND NEW.status != 'completed' THEN
        NEW.status := 'completed';
    END IF;
    
    -- If completed_at is removed, allow status to change
    IF NEW.completed_at IS NULL AND OLD.completed_at IS NOT NULL THEN
        -- Allow status to be changed (e.g., back to in_progress if needed)
        -- Don't auto-update in this case
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update status
DROP TRIGGER IF EXISTS trigger_update_interview_status ON interviews;
CREATE TRIGGER trigger_update_interview_status
    BEFORE UPDATE ON interviews
    FOR EACH ROW
    WHEN (NEW.completed_at IS NOT NULL AND NEW.status != 'completed')
    EXECUTE FUNCTION update_interview_status_on_completion();

