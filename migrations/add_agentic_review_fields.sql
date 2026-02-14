-- Add agentic review fields to agents table
-- Migration: Add reviewed_at and review_reason columns

ALTER TABLE agents 
ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP;

ALTER TABLE agents 
ADD COLUMN IF NOT EXISTS review_reason TEXT;

-- Create index on reviewed_at for analytics
CREATE INDEX IF NOT EXISTS idx_agents_reviewed_at ON agents(reviewed_at);

-- Update existing agents with null review fields to have defaults
UPDATE agents 
SET reviewed_at = created_at, 
    review_reason = 'Legacy agent - pre-agentic review'
WHERE reviewed_at IS NULL 
  AND pending_review = FALSE;
